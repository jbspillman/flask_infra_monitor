from datetime import datetime, timedelta
import random
import json
import os


script_folder = os.path.dirname(os.path.abspath(__file__))
servers_folder = os.path.join(script_folder, 'server_fleet')
os.makedirs(servers_folder, exist_ok=True)


def create_fake_servers():

    devices_json = os.path.join(servers_folder, 'devices.json')
    if os.path.exists(devices_json):
        with open(devices_json, 'r', encoding="utf-8") as file:
            device_list = json.load(file)
        return device_list

    ''' these are just randomly generated sites and products. '''
    site_options = [
        "na-us-north-east-01",
        "na-us-north-east-02",
        "na-us-north-west-01",
        "na-us-north-west-02",
        "em-uk-north-east-01",
        "em-uk-north-east-02",
        "ap-sg-north-west-01",
        "ap-sg-north-west-02",
        "ap-jp-north-west-01",
        "ap-jp-north-west-02"
    ]
    ''' device will start with this identifier. '''
    server_product_vendors = {
        "Dell PowerScale":  "ps",
        "Dell PowerEdge": "pe",
        "NetApp SolidFire": "sf",
        "NetApp ONTAP": "ot",
        "NetApp StorageGRID": "sg",
        "VAST Data": "vd",
        "Pure FlashBlade": "pf",
        "Qumulo": "qu",
        "MinIO": "mi"
    }
    envs = ["pr"]

    sites_count = len(site_options)
    products_count = len(server_product_vendors)
    devices_per_product = 4
    totals = sites_count * products_count * devices_per_product

    print("products_count:".ljust(30), products_count)
    print("sites_count:".ljust(30), sites_count)
    print("devices_per_product:".ljust(30), devices_per_product)
    print("totals:".ljust(30), totals)

    device_list = []
    for site in site_options:
        split_site = site.split('-')

        site_id = f'{split_site[0]}{split_site[1]}{split_site[2][0]}{split_site[3][0]}{split_site[4]}'
        site_folder = os.path.join(servers_folder, site)
        os.makedirs(site_folder, exist_ok=True)

        for vendor_product, device_prefix in server_product_vendors.items():
            y = 0
            while y != devices_per_product:
                y += 1
                pyn = str(y).zfill(3)
                for env in envs:
                    device_name_number = f'{device_prefix}{env}{pyn}'
                    full_device = f'{site_id}{device_name_number}'

                    dti = {
                        "site_name": site,
                        "product_name": vendor_product,
                        "environment": env,
                        "device_name": full_device
                    }
                    if dti not in device_list:
                        device_list.append(dti)
                        dv_file = os.path.join(site_folder, f'{full_device}.json')
                        if not os.path.exists(dv_file):
                            p_dti = json.dumps(dti, indent=4)
                            with open(dv_file, 'w', encoding="utf-8") as f:
                                f.write(p_dti)

    p_device_list = json.dumps(device_list, indent=4)
    with open(devices_json, 'w', encoding="utf-8") as f:
        f.write(p_device_list)
    return device_list


def generate_fake_performance_data():
    performance_data = []
    
    # Generate data for past 3 months, every 1 minute, excluding current day
    days_back = 91  # 3 months + 1 day to exclude today
    
    # Start from 91 days ago, end at beginning of today
    start_time = datetime.now() - timedelta(days=days_back)
    end_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  # Start of today
    
    # Calculate total minutes between start and end (excluding today)
    total_minutes = int((end_time - start_time).total_seconds() // 60)
    
    for i in range(total_minutes):
        # Create timestamp for each minute
        timestamp = start_time + timedelta(minutes=i)
        date_log_stamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if timestamp is in peak hours (8:00 AM - 1:00 PM)
        hour = timestamp.hour
        is_peak_hours = 8 <= hour < 13
        
        # Define multipliers for peak vs off-peak hours
        if is_peak_hours:
            # Higher values during peak hours
            cpu_multiplier = 1.4  # 40% higher
            memory_multiplier = 1.3  # 30% higher
            disk_multiplier = 1.5  # 50% higher
            latency_multiplier = 1.6  # 60% higher (higher latency = worse performance)
            process_multiplier = 1.4  # 40% more processes
        else:
            # Normal values during off-peak hours
            cpu_multiplier = 1.0
            memory_multiplier = 1.0
            disk_multiplier = 1.0
            latency_multiplier = 1.0
            process_multiplier = 1.0
        
        # Generate base values and apply multipliers
        base_cpu = random.uniform(10.0, 70.0)  # Lower base to allow for peak scaling
        base_memory = random.uniform(2.0, 12.0)
        base_disk = random.uniform(50.0, 350.0)
        base_latency = random.uniform(1.0, 60.0)
        base_processes = random.randint(50, 150)
        
        data = {
            "timestamp": date_log_stamp,
            "cpu_usage_percent": round(min(99.0, base_cpu * cpu_multiplier), 2),
            "memory_usage_gb": round(min(16.0, base_memory * memory_multiplier), 2),
            "disk_io_mbps": round(min(500.0, base_disk * disk_multiplier), 2),
            "network_latency_ms": round(min(100.0, base_latency * latency_multiplier), 2),
            "process_count": min(200, int(base_processes * process_multiplier))
        }
        performance_data.append(data)
    
    return performance_data


def generate_performance_stats():
    # Generate minute-by-minute data for past 3 months
    
    # print("Generating performance data for past 3 months (every 1 minute)...")
    data = generate_fake_performance_data()
    
    # Print summary and examples
    # print(f"Total entries generated: {len(data):,}")
    # print(f"Date range: {data[0]['timestamp']} to {data[-1]['timestamp']}")
    
    # Show some peak vs off-peak examples
    # print("\nSample entries:")
    # peak_examples = [entry for entry in data if "08:" in entry['timestamp'] or "09:" in entry['timestamp']][:5]
    # offpeak_examples = [entry for entry in data if "02:" in entry['timestamp'] or "03:" in entry['timestamp']][:5]
    
    # print("\nPeak hours examples (8-9 AM):")
    # for entry in peak_examples:
        # print(f"{entry['timestamp']} - CPU: {entry['cpu_usage_percent']}%, "
        #     f"Memory: {entry['memory_usage_gb']}GB, Latency: {entry['network_latency_ms']}ms")
    
    # print("\nOff-peak hours examples (2-3 AM):")
    # for entry in offpeak_examples:
        # print(f"{entry['timestamp']} - CPU: {entry['cpu_usage_percent']}%, "
        #     f"Memory: {entry['memory_usage_gb']}GB, Latency: {entry['network_latency_ms']}ms")
              
    return data
              

def update_performance_stats(devices_list):

    device_updates_count = 0
    for device in devices_list:
        stats = generate_performance_stats()
        count_of_stats = len(stats)

        site_name = device["site_name"]
        device_name = device["device_name"]
        site_folder = os.path.join(servers_folder, site_name)
        os.makedirs(site_folder, exist_ok=True)
        print(site_name, device_name, count_of_stats)
        
        device_file_path = os.path.join(site_folder, f'{device_name}.json')
        stats_data = []
        if os.path.exists(device_file_path):
            with open(device_file_path, 'r', encoding="utf-8") as file:
                data = json.load(file)
                try:
                    stats_data = data["statistics"]
                except KeyError:
                    pass
        stats_data.extend(stats)
        new_json_data =  {
            "device_info": device,
            "statistics": stats_data
        }
        device_updates_count += 1
        print(device_updates_count, device)
        p_new_json_data = json.dumps(new_json_data, indent=4)
        with open(device_file_path, 'w', encoding="utf-8") as f:
            f.write(p_new_json_data)
            
    return device_updates_count    
 
devices = create_fake_servers()
update_performance_stats(devices)

