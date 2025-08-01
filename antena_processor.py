from ssh_client import get_antenna_data
from data_parsers import parse_top_data, parse_net_dev, parse_ifconfig_data, parse_uptime_data, parse_system_cfg_data, parse_airmax_data, parse_date_data, format_uptime
import firebase_admin
from firebase_admin import db
import time
import json

async def process_antenna(antenna_id, antenna_data):
    ip = antenna_data['ip']
    username = antenna_data['usuario_ssh']
    password = antenna_data['password_ssh']

    top_data = await get_antenna_data(ip, username, password, 'top -b -n1 | head -5')
    net_dev_data = await get_antenna_data(ip, username, password, 'cat /proc/net/dev')
    ifconfig_data = await get_antenna_data(ip, username, password, 'ifconfig')
    uptime_data = await get_antenna_data(ip, username, password, 'uptime')
    system_cfg_data = await get_antenna_data(ip, username, password, 'cat /tmp/system.cfg')
    date_data = await get_antenna_data(ip, username, password, 'date')
    airmax_data = await get_antenna_data(ip, username, password, 'ubntbox cmd --airmax-status')

    cpu, mem_used, mem_free, cpu_details = parse_top_data(top_data) if top_data else (None, None, None, {})
    rx_bytes, tx_bytes, rx_packets_net, tx_packets_net = parse_net_dev(net_dev_data) if net_dev_data else (None, None, None, None)
    rx_packets_if, tx_packets_if, rx_dropped, tx_dropped, wlan0_mac, lan0_mac = parse_ifconfig_data(ifconfig_data) if ifconfig_data else (None, None, None, None, None, None)
    uptime_seconds = parse_uptime_data(uptime_data) if uptime_data else None
    uptime_formatted = format_uptime(uptime_seconds)
    system_cfg_parsed = parse_system_cfg_data(system_cfg_data) if system_cfg_data else {}
    airmax_parsed = parse_airmax_data(airmax_data) if airmax_data else {}
    date = parse_date_data(date_data) if date_data else None

    memory_usage = None
    if mem_used is not None and mem_free is not None:
        total_mem = mem_used + mem_free
        if total_mem > 0:
            memory_usage = f"{(mem_used / total_mem * 100):.1f} %"

    antenna_data_dict = {}
    if mem_used is not None and mem_free is not None:
        antenna_data_dict['Rendimiento'] = {'Memoria_Usada': f"{mem_used:.1f} MB", 'Memoria_Libre': f"{mem_free:.1f} MB", 'Uso_Memoria': memory_usage}
    if cpu_details:
        antenna_data_dict['Uso_de_CPU_Detallado'] = {k: f"{v}%" for k, v in cpu_details.items()}
    if cpu is not None:
        antenna_data_dict['Uso_de_CPU'] = {'Uso_Total': cpu}
    if rx_bytes is not None and tx_bytes is not None:
        bajada_mb = (rx_bytes / 1_048_576) * 8
        subida_mb = (tx_bytes / 1_048_576) * 8
        antenna_data_dict['Trafico_de_Datos'] = {
            'Bajada': f"{bajada_mb:.1f} Mb",
            'Subida': f"{subida_mb:.1f} Mb",
            'Paquetes_Perdidos': f"{rx_dropped or 0} (Bajada), {tx_dropped or 0} (Subida)" if rx_dropped is not None or tx_dropped is not None else None
        }
    if any([system_cfg_parsed.get('ssid'), system_cfg_parsed.get('device_name'), system_cfg_parsed.get('netmask_mode'),
            system_cfg_parsed.get('wireless_mode'), system_cfg_parsed.get('security'), date, uptime_formatted,
            system_cfg_parsed.get('channel_freq'), system_cfg_parsed.get('bandwidth'),
            system_cfg_parsed.get('tx_power'), system_cfg_parsed.get('antenna'),
            system_cfg_parsed.get('ap_mac'), system_cfg_parsed.get('signal_strength'),
            system_cfg_parsed.get('noise_threshold'), system_cfg_parsed.get('ccq')]):
        antenna_data_dict['Estado_General'] = {
            k: v for k, v in {
                'AP_Asociado': system_cfg_parsed.get('ssid'),
                'Nombre_Dispositivo': system_cfg_parsed.get('device_name'),
                'Modo_Mascara_Red': system_cfg_parsed.get('netmask_mode'),
                'Modo_Inalambrico': system_cfg_parsed.get('wireless_mode'),
                'Seguridad': system_cfg_parsed.get('security'),
                'Fecha': date,
                'Tiempo_Encendido': uptime_formatted,
                'Canal_Frecuencia': system_cfg_parsed.get('channel_freq'),
                'Ancho_de_Canal': system_cfg_parsed.get('bandwidth'),
                'Potencia_TX': system_cfg_parsed.get('tx_power'),
                'Antena': system_cfg_parsed.get('antenna'),
                'WLAN0_MAC': wlan0_mac,
                'LAN0_MAC': lan0_mac,
                'AP_MAC': system_cfg_parsed.get('ap_mac'),
                'Intensidad_Senal': system_cfg_parsed.get('signal_strength'),
                'Umbral_Ruido': system_cfg_parsed.get('noise_threshold'),
                'Transmitir_CCQ': system_cfg_parsed.get('ccq'),
                'Ultima_Actualizacion': time.strftime('%H:%M:%S %d/%m/%Y', time.localtime())
            }.items() if v is not None
        }
    if airmax_parsed:
        antenna_data_dict['AirMAX'] = airmax_parsed

    def sanitize_key(key):
        return ''.join(c if c not in '$#[]/.' else '_' for c in key)

    antenna_data_dict = {sanitize_key(k): {sanitize_key(sk): sv for sk, sv in v.items()} for k, v in antenna_data_dict.items()}

    return {
        'nombre': antenna_data['nombre'],
        'ip': ip, 
        **antenna_data_dict
    }

async def aggregate_and_upload_antennas(antennas_data):
    timestamp = time.strftime('%Y-%m-%d %H:%M %p', time.localtime())
    aggregated_data = {
        'timestamp': timestamp,
        'antennas': [data for data in antennas_data if data]  
    }

    ref = db.reference('antenas/aggregated_data')
    try:
        ref.update({'antennas': aggregated_data['antennas']})
        print(f"Datos de todas las antenas actualizados con timestamp: {timestamp}")
    except Exception as e:
        print(f"Error al actualizar datos agregados: {e}")