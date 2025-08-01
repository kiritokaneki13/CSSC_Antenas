import time
import json

def parse_top_data(data):
    cpu = mem_used = mem_free = None
    cpu_details = {}
    for line in data.split('\n') if data else []:
        if line.startswith('Mem:'):
            parts = line.split()
            try:
                mem_used = int(parts[1].replace('K', '')) / 1024
                mem_free = int(parts[3].replace('K', '')) / 1024
            except (IndexError, ValueError):
                pass
        elif line.startswith('CPU:'):
            parts = line.split()
            try:
                cpu_usage = 100 - int(parts[7].replace('%', '')) if len(parts) > 7 else 0
                cpu_details = {
                    'Uso_por_Usuario': int(parts[1].replace('%', '')) if len(parts) > 1 else 0,
                    'Uso_por_Sistema': int(parts[3].replace('%', '')) if len(parts) > 3 else 0,
                    'Uso_por_NIC': int(parts[5].replace('%', '')) if len(parts) > 5 else 0,
                    'Tiempo_Ocioso': int(parts[7].replace('%', '')) if len(parts) > 7 else 0,
                    'Uso_por_E_S': int(parts[9].replace('%', '')) if len(parts) > 9 else 0,
                    'Interrupciones': int(parts[11].replace('%', '')) if len(parts) > 11 else 0,
                    'Interrupciones_Soft': int(parts[13].replace('%', '')) if len(parts) > 13 else 0
                }
                cpu = f"{cpu_usage}%"
            except (IndexError, ValueError):
                pass
    return cpu, mem_used, mem_free, cpu_details

def parse_net_dev(data):
    rx_bytes = tx_bytes = rx_packets = tx_packets = None
    for line in data.split('\n') if data else []:
        if line.startswith('  ath0:'):
            parts = line.split()
            try:
                rx_bytes = int(parts[1])
                rx_packets = int(parts[2])
                tx_bytes = int(parts[9])
                tx_packets = int(parts[10])
            except (IndexError, ValueError):
                pass
    return rx_bytes, tx_bytes, rx_packets, tx_packets

def parse_ifconfig_data(data):
    rx_packets = tx_packets = rx_dropped = tx_dropped = None
    wlan0_mac = lan0_mac = None
    for line in data.split('\n') if data else []:
        if 'ath0' in line:
            next_line = next((l for l in data.split('\n')[data.split('\n').index(line) + 1:] if 'RX packets' in l), None)
            if next_line:
                parts = next_line.split()
                try:
                    rx_packets = int(parts[0])
                    tx_packets = int(parts[4])
                    rx_dropped = int(parts[3].split('dropped:')[1]) if 'dropped' in next_line else 0
                    tx_dropped = int(parts[7].split('overruns:')[1]) if 'overruns' in next_line else 0
                except (IndexError, ValueError, AttributeError):
                    pass
        elif 'HWaddr' in line and 'ath0' in line:
            wlan0_mac = line.split('HWaddr ')[1].strip()
        elif 'HWaddr' in line and 'eth0' in line:
            lan0_mac = line.split('HWaddr ')[1].strip()
    return rx_packets, tx_packets, rx_dropped, tx_dropped, wlan0_mac, lan0_mac

def parse_uptime_data(data):
    uptime_seconds = None
    for line in data.split('\n') if data else []:
        if 'up' in line:
            try:
                parts = line.split('up ')[1].split(',')
                uptime_part = parts[0].strip().split()
                days = int(uptime_part[0].split('days')[0]) if 'days' in uptime_part[0] else 0
                time_part = uptime_part[-1].split(':')
                hours = int(time_part[0])
                minutes = int(time_part[1])
                uptime_seconds = (days * 86400) + (hours * 3600) + (minutes * 60)
            except (IndexError, ValueError):
                pass
    return uptime_seconds

def parse_system_cfg_data(data):
    parsed_data = {}
    for line in data.split('\n') if data else []:
        if 'resolv.host.1.name' in line:
            parsed_data['device_name'] = line.split('=')[1].strip()
        elif 'netconf.1.netmask' in line and '255.255.255.0' in line:
            parsed_data['netmask_mode'] = 'Enrutador'
        elif 'wireless.1.mode' in line:
            parsed_data['wireless_mode'] = line.split('=')[1].strip().replace('managed', 'Estación').replace('sta-wds', 'Estación WDS')
        elif 'wireless.1.ssid' in line:
            parsed_data['ssid'] = line.split('=')[1].strip()
        elif 'wireless.1.security.type' in line:
            parsed_data['security'] = line.split('=')[1].strip().replace('WPA-PSK', 'WPA2-AES').replace('none', 'Sin seguridad')
        elif 'radio.1.channel' in line:
            parsed_data['channel_freq'] = line.split('=')[1].strip() + ' MHz'
        elif 'radio.1.chanbw' in line:
            parsed_data['bandwidth'] = line.split('=')[1].strip() + ' MHz'
        elif 'radio.1.txpower' in line:
            parsed_data['tx_power'] = line.split('=')[1].strip() + ' dBm'
        elif 'radio.1.antenna.gain' in line:
            parsed_data['antenna'] = f"{line.split('=')[1].strip()}x14 - 23 dBi"
        elif 'ap.mac' in line:
            parsed_data['ap_mac'] = line.split('=')[1].strip()
        elif 'signal' in line and not 'signal_led' in line:
            parsed_data['signal_strength'] = line.split('=')[1].strip() + ' dBm'
        elif 'noise' in line:
            parsed_data['noise_threshold'] = line.split('=')[1].strip() + ' dBm'
        elif 'wireless.1.ccq' in line:
            parsed_data['ccq'] = line.split('=')[1].strip() + ' %'
    return parsed_data

def parse_airmax_data(data):
    airmax_data = {}
    if data:
        for line in data.split('\n'):
            if 'airMAX' in line:
                try:
                    key, value = line.split(':')
                    airmax_data[key.strip().replace(' ', '_')] = value.strip()
                except ValueError:
                    pass
    return airmax_data

def parse_date_data(data):
    date = None
    for line in data.split('\n') if data else []:
        if line.strip():
            try:
                date = line.strip()
            except (IndexError, ValueError):
                pass
    return date

def format_uptime(uptime_seconds):
    if not uptime_seconds:
        return None
    if uptime_seconds >= 86400:
        days = uptime_seconds // 86400
        return f"{days} día{'s' if days > 1 else ''}"
    elif uptime_seconds >= 3600:
        hours = uptime_seconds // 3600
        return f"{hours} hora{'s' if hours > 1 else ''}"
    else:
        minutes = uptime_seconds // 60
        return f"{minutes} minuto{'s' if minutes > 1 else ''}"