from performance_chart_generator import create_report_from_file
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from datetime import datetime, timedelta
from collections import defaultdict
from itertools import groupby
from operator import itemgetter
from json2html import *
import json
import os

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'my-ever-so-so-secret-key-goes-here'

APP_ROOT = os.getcwd()
static_folder = os.path.join(APP_ROOT, 'static')
json_folder =  os.path.join(static_folder, 'json')
charts_folder =  os.path.join(static_folder, 'charts')
os.makedirs(static_folder, exist_ok=True)
os.makedirs(json_folder, exist_ok=True)
os.makedirs(charts_folder, exist_ok=True)

site_product_data_map_json = os.path.join(charts_folder, '__site_products_map.json')
remote_servers = os.path.join(APP_ROOT, 'server_fleet')


def is_file_older_than_minutes(file_path, minutes):
    """
    Checks if a file is older than a specified number of minutes.

    Args:
        file_path (str): The path to the file.
        minutes (int): The age threshold in minutes.

    Returns:
        bool: True if the file is older than the specified minutes, False otherwise.
    """
    if not os.path.exists(file_path):
        return False  # Or raise an error, depending on desired behavior

    # Get the last modification time of the file as a timestamp
    modification_timestamp = os.path.getmtime(file_path)

    # Convert the timestamp to a datetime object
    modification_time = datetime.fromtimestamp(modification_timestamp)

    # Get the current time
    current_time = datetime.now()

    # Calculate the age of the file
    file_age = current_time - modification_time

    # Define the age threshold
    age_threshold = timedelta(minutes=minutes)

    # Compare the file's age with the threshold
    return file_age > age_threshold


def convert_json_to_table(data_is_json):
    html_table = json2html.convert(json=data_is_json)
    return html_table


def create_chart_site_map(site_map_file_path, just_map_list=False):
    ''' generate the site mapping file from arg: site_map_file_path'''

    if not just_map_list:
        with open(site_map_file_path, "r", encoding="utf-8") as json_input:
            site_product_data_list = json.load(json_input)
        return site_product_data_list


    servers_list_file = os.path.join(remote_servers, 'devices.json')
    with open(servers_list_file, "r", encoding="utf-8") as json_input:
        servers_data = json.load(json_input)

    sites_list = []
    products_list = []
    devices_list = []
    for item in servers_data:
        site_name = item["site_name"]
        product_name = item["product_name"]
        device_name = item["device_name"]
        sites_list.append(site_name)
        products_list.append(product_name)
        devices_list.append(device_name)

    sites_list = sorted(set(sites_list))
    products_list = sorted(set(products_list))
    devices_list = sorted(set(devices_list))
    print("sites_list:", len(sites_list))
    print("products_list:", len(products_list))
    print("devices_list:", len(devices_list))

    site_product_data_list = []
    z = 0
    for site_name in sites_list:           
        for product_name in products_list:
            k = {
                "site_name": site_name,
                "product_name": product_name,
            }
            if k not in site_product_data_list:
                print('adding to site map:'.ljust(30), k)
                site_product_data_list.append(k)

    p_site_product_data_map = json.dumps(site_product_data_list, indent=4)
    with open(site_map_file_path, 'w', encoding="utf-8") as f:
        f.write(p_site_product_data_map)
    return site_product_data_list


@app.route('/')
def index():
    return render_template('index.html', title='Home Page')


@app.route('/about')
def about():
    return render_template('about.html', title='About This')


@app.route('/standard_reports')
def standard_reports():
    return render_template('standard_reports.html', title='Standard Reports')


@app.route('/v1', methods=['GET'])
def v1():
    return jsonify({'api_code': 200, 'message': 'v1 endpoints are Online.'})


@app.route('/v1/fetch_json')  #  methods=['GET', 'POST']
def fetch_json():
    if not request.args.get('file'):
        err_dict = {'api_code': 404, 'message': '?file=<YOUR_FILE.JSON>'}
        return jsonify(err_dict), 404
    else:
        json_file_name = request.args.get('file')  # Get a single value
        json_path_value = os.path.join(json_folder, json_file_name)

        if json_file_name.lower().endswith('.json'):
            with open(json_path_value, 'r') as json_file:
                data = json.load(json_file)
            html_table = convert_json_to_table(data)
            html_table += '\n <br><br>end of content...'

            success_dict = {
                'api_code': 200,
                'message': "success",
                'json': data,
                'html': html_table
            }
            return jsonify(success_dict), 200

        else:
            print('ERROR: file name:', f'[{json_file_name}]')
            err_dict = {'api_code': 404, 'message': 'file is not available for download.'}
            return jsonify(err_dict)


@app.route('/v1/fetch_chart')
def fetch_chart():

    if not request.args.get('site_name') or request.args.get('site_name') is None:
        err_dict = {'api_code': 404, 'message': '?site_name=<SITE_NAME>?product_name=<PRODUCT_NAME>'}
        return jsonify(err_dict), 404
    else:
        chart_site_name = request.args.get('site_name')
        
    if not request.args.get('product_name') or request.args.get('product_name') == "undefined" or request.args.get('product_name') is None:
        err_dict = {'api_code': 404, 'message': '?site_name=<SITE_NAME>?product_name=<PRODUCT_NAME>'}
        return jsonify(err_dict), 404
    else:
        chart_product_name = request.args.get('product_name')        

    file_name_base = f'{chart_site_name}__{chart_product_name}'
    chart_html_file = os.path.join(charts_folder, f'{file_name_base}.html')
    chart_json_file = os.path.join(charts_folder, f'{file_name_base}.json')
    
    regen_html_json = False
    if not os.path.exists(chart_html_file):
        regen_html_json = True
    else:
        is_old = is_file_older_than_minutes(chart_html_file, 5)
        if is_old:
            regen_html_json = True

    if not os.path.exists(chart_json_file):
        regen_html_json = True
    else:
        is_old = is_file_older_than_minutes(chart_json_file, 5)
        if is_old:
            regen_html_json = True    
    
    if regen_html_json:

        servers_list_file = os.path.join(remote_servers, 'devices.json')
        with open(servers_list_file, "r", encoding="utf-8") as json_input:
            servers_data = json.load(json_input)

        site_product_json = os.path.join(charts_folder, f"{chart_site_name}__{chart_product_name}.json")
        site__product_stats = []
        for item in servers_data:
            if item["site_name"] == chart_site_name and item["product_name"] == chart_product_name:
                device_name = item["device_name"]
                device_file = os.path.join(remote_servers, chart_site_name, f'{device_name}.json')
                print('getting data from server:'.ljust(30), device_name)
        
                with open(device_file, "r", encoding="utf-8") as json_input:
                    server_info = json.load(json_input)
                stats_dict = {
                    server_info["device_info"]["device_name"]: server_info["statistics"]
                }
                if stats_dict not in site__product_stats:
                    site__product_stats.append(stats_dict)

        p_site_stats = json.dumps(site__product_stats, indent=4)
        with open(site_product_json, 'w', encoding="utf-8") as f:
            f.write(p_site_stats)
        print('wrote chart data json:'.ljust(30), f"{chart_site_name}__{chart_product_name}.json")
        
        ''' generate report from the data '''
        create_report_from_file(chart_json_file, chart_html_file)        

    ''' we have report, just return parsed html content. '''
    html_content = "<p>no data</p>"
    with open(chart_html_file, 'r') as html_file:
        html_content = html_file.read()

    success_dict = {
        'api_code': 200,
        'message': "success",
        'chart_path_value': chart_html_file,
        'html': html_content
    }
    return jsonify(success_dict), 200


@app.route("/v1/fetch_json/")
def choice_json():
    return redirect(url_for('fetch_json'))


@app.route('/v1/fetch_performance_charts', methods=['GET'])
def fetch_performance_charts():
    
    regen_file = False
    if not os.path.exists(site_product_data_map_json):
        regen_file = True
    else:
        is_old = is_file_older_than_minutes(site_product_data_map_json, 9)
        if is_old:
            regen_file = True

    if regen_file:
        ''' generates list of available devies and will create files if they don't exist. '''
        site_product_data_map = create_chart_site_map(site_product_data_map_json, True)
    else:
        with open(site_product_data_map_json, "r", encoding="utf-8") as json_input:
            site_product_data_map = json.load(json_input)
        
    ''' generate options menu from the available devices in inventory. '''
    unique_options = []
    for item in site_product_data_map:
        site_name = item["site_name"]
        product_name = item["product_name"]
        this_option = f'{site_name.upper()} : {product_name}'
        if this_option not in unique_options:
            unique_options.append(this_option)
    unique_options = sorted(unique_options)

    html_options = '<option selected value="NONE">---------- Select Chart ----------</option>\n'
    for option_value in unique_options:
        opt_str = f'<option value="{option_value}">{option_value}</option>\n'
        html_options += opt_str
    return jsonify({'api_code': 200, 'map_list': html_options})


@app.route("/v1/fetch_performance_charts/")
def choice_performance_charts():
    return redirect(url_for('fetch_performance_charts'))


@app.route('/performance_charts', methods=['GET'])
def performance_charts():
    return render_template('performance_charts.html', title='Performance Charts')


@app.errorhandler(404)
def page_not_found(e):
    err_dict = {'api_code': 404, 'message': 'PAGE NOT EXIST.'}
    return jsonify(err_dict), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9999)

    