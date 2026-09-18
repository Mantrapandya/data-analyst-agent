import urllib.request
import json

base = 'http://127.0.0.1:5002'

def test():
    # 1. Health
    req = urllib.request.urlopen(f'{base}/api/health')
    health = json.loads(req.read().decode())
    print('[OK] Health:', health)

    # 2. Multi-dataset test: HR
    data = json.dumps({'type': 'hr'}).encode('utf-8')
    req = urllib.request.Request(f'{base}/api/sample', data=data, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    hr_ds = json.loads(res.read().decode())
    print('[OK] HR Sample Loaded:', hr_ds['dataset']['original_filename'])

    # 3. Get HR Insights
    req = urllib.request.urlopen(f"{base}/api/datasets/{hr_ds['dataset']['id']}/insights")
    hr_insights = json.loads(req.read().decode())
    print('[OK] HR KPIs:', [k['title'] for k in hr_insights['kpis']])

    # 4. Multi-dataset test: Real Estate
    data = json.dumps({'type': 'real_estate'}).encode('utf-8')
    req = urllib.request.Request(f'{base}/api/sample', data=data, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    re_ds = json.loads(res.read().decode())
    print('[OK] Real Estate Sample Loaded:', re_ds['dataset']['original_filename'])

    # 5. Get Real Estate Insights
    req = urllib.request.urlopen(f"{base}/api/datasets/{re_ds['dataset']['id']}/insights")
    re_insights = json.loads(req.read().decode())
    print('[OK] Real Estate KPIs:', [k['title'] for k in re_insights['kpis']])

if __name__ == '__main__':
    test()
