"""
SIKD/DJPK Client — Akses data APBD dari DJPK Kemenkeu
Data publik tanpa autentikasi.
"""

import requests
import xml.etree.ElementTree as ET
import re

BASE_URL = "https://djpk.kemenkeu.go.id/portal"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*',
}

_session = requests.Session()
_session.headers.update(HEADERS)


def get_provinsi(tahun):
    """Get list of provinces for a given year."""
    r = _session.get(f"{BASE_URL}/provinsi/{tahun}", timeout=15)
    r.raise_for_status()
    data = r.json()
    result = []
    for kode, nama in data.items():
        result.append({"kode": kode, "nama": nama})
    return result


def get_pemda(provinsi_kode, tahun):
    """Get list of local governments for a province and year."""
    r = _session.get(f"{BASE_URL}/pemda/{provinsi_kode}/{tahun}", timeout=15)
    r.raise_for_status()
    data = r.json()
    result = []
    for kode, nama in data.items():
        result.append({"kode": kode, "nama": nama})
    return result


def get_apbd(tahun, provinsi='--', pemda='--', periode='12'):
    """
    Get APBD data. Returns parsed data from XML spreadsheet.
    periode: 1-12 (bulan realisasi)
    provinsi/pemda: kode or '--' for all
    """
    url = f"{BASE_URL}/csv_apbd"
    params = {
        'type': 'apbd',
        'periode': periode,
        'tahun': tahun,
        'provinsi': provinsi,
        'pemda': pemda,
    }

    r = _session.get(url, params=params, timeout=30)
    r.raise_for_status()

    content = r.text.strip()
    if not content or '<Workbook' not in content:
        return {'error': 'Data tidak tersedia untuk parameter yang dipilih', 'rows': []}

    return _parse_xml_spreadsheet(content)


def get_apbd_compare(tahun_list, provinsi, pemda, periode='12'):
    """Get APBD data for multiple years for comparison."""
    results = {}
    for tahun in tahun_list:
        try:
            data = get_apbd(tahun, provinsi, pemda, periode)
            results[str(tahun)] = data
        except Exception as e:
            results[str(tahun)] = {'error': str(e), 'rows': []}
    return results


def _parse_xml_spreadsheet(xml_text):
    """Parse XML Spreadsheet format from DJPK into structured data."""
    # Fix namespace issues
    xml_text = re.sub(r'xmlns="[^"]*"', '', xml_text)
    xml_text = re.sub(r'ss:', '', xml_text)

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {'error': 'Gagal parse data XML', 'rows': []}

    rows = []
    all_rows = root.findall('.//Row')

    if not all_rows:
        return {'error': 'Tidak ada data', 'rows': []}

    # First row is header
    headers = []
    for cell in all_rows[0].findall('Cell'):
        data_el = cell.find('Data')
        headers.append(data_el.text.strip() if data_el is not None and data_el.text else '')

    # Data rows
    for row_el in all_rows[1:]:
        cells = row_el.findall('Cell')
        row = {}
        for i, cell in enumerate(cells):
            data_el = cell.find('Data')
            if data_el is not None and data_el.text:
                val = data_el.text.strip()
                data_type = cell.get('Type', '') or (data_el.get('Type', ''))
                if data_type == 'Number':
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                if i < len(headers) and headers[i]:
                    row[headers[i]] = val
                else:
                    row[f'col_{i}'] = val
            elif i < len(headers) and headers[i]:
                row[headers[i]] = ''

        if row:
            rows.append(row)

    # Categorize rows
    categorized = []
    for row in rows:
        akun = str(row.get('Akun', '')).strip()
        level = 0
        if akun.startswith('  '):
            level = 2
        elif akun.startswith(' '):
            level = 1

        anggaran = row.get('Anggaran', 0)
        realisasi = row.get('Realisasi', 0)
        persentase = row.get('Persentase', '')

        categorized.append({
            'akun': akun.strip(),
            'level': level,
            'anggaran': anggaran if isinstance(anggaran, (int, float)) else 0,
            'realisasi': realisasi if isinstance(realisasi, (int, float)) else 0,
            'persentase': str(persentase),
        })

    return {
        'headers': headers,
        'rows': categorized,
        'total_rows': len(categorized),
    }


def close():
    _session.close()
