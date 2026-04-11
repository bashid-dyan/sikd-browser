"""
SIKD Browser — Flask Web App
Jelajahi data APBD dari DJPK Kemenkeu
"""

import os
import atexit
from flask import Flask, request, jsonify, render_template
import sikd_client

app = Flask(__name__, static_folder='static', static_url_path='/static')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/provinsi')
def api_provinsi():
    tahun = request.args.get('tahun', '2025')
    try:
        data = sikd_client.get_provinsi(tahun)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pemda')
def api_pemda():
    provinsi = request.args.get('provinsi', '')
    tahun = request.args.get('tahun', '2025')
    if not provinsi:
        return jsonify({'error': 'Parameter provinsi harus diisi'}), 400
    try:
        data = sikd_client.get_pemda(provinsi, tahun)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/apbd')
def api_apbd():
    tahun = request.args.get('tahun', '2025')
    provinsi = request.args.get('provinsi', '--')
    pemda = request.args.get('pemda', '--')
    periode = request.args.get('periode', '12')
    try:
        data = sikd_client.get_apbd(tahun, provinsi, pemda, periode)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare')
def api_compare():
    tahun_str = request.args.get('tahun', '')  # comma-separated: 2023,2024,2025
    provinsi = request.args.get('provinsi', '--')
    pemda = request.args.get('pemda', '--')
    periode = request.args.get('periode', '12')

    if not tahun_str:
        return jsonify({'error': 'Parameter tahun harus diisi (misal: 2023,2024,2025)'}), 400

    tahun_list = [t.strip() for t in tahun_str.split(',') if t.strip()]
    try:
        data = sikd_client.get_apbd_compare(tahun_list, provinsi, pemda, periode)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


atexit.register(sikd_client.close)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
