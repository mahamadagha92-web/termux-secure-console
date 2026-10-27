from flask import Flask, jsonify, render_template_string, request, send_from_directory, redirect, make_response
import subprocess, os, threading, time
app = Flask(__name__)
ADMIN_USER, ADMIN_PASS, AUTH_TOKEN, STORAGE_DIR = 'admin', 'termux2026', 'secure_token_abc123', '/root/public_site'
watchdog_cache = []

def watchdog():
    global watchdog_cache
    while True:
        try:
            out = subprocess.check_output(['ip', 'neigh', 'show']).decode()
            tmp = []
            for l in out.splitlines():
                if 'REACHABLE' in l or 'STALE' in l:
                    p = l.split()
                    if len(p) >= 5: tmp.append({'ip':p, 'mac':p})
            watchdog_cache = tmp
        except: pass
        time.sleep(15)
threading.Thread(target=watchdog, daemon=True).start()

def is_auth(): return request.cookies.get('session_auth') == AUTH_TOKEN

UI = '<html><head><title>Console</title><style>body{font-family:sans-serif;background:#0f172a;color:#f8fafc;margin:40px;}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:1000px;margin:0 auto;}.card{background:#1e293b;padding:25px;border-radius:12px;border:1px solid #334155;}h1,h3{color:#38bdf8;margin:0 0 10px;}a{color:#4ade80;text-decoration:none;}input{width:80%;padding:10px;background:#0f172a;border:1px solid #334155;color:#4ade80;border-radius:6px;font-family:monospace;}button{padding:10px 20px;background:#38bdf8;color:#0f172a;border:none;font-weight:bold;border-radius:6px;cursor:pointer;}.term-box{background:#0f172a;padding:15px;border-radius:6px;font-family:monospace;color:#fbbf24;white-space:pre-wrap;margin-top:15px;max-height:250px;overflow-y:auto;}</style></head><body><div class=\"grid\"><div class=\"card full-width\"><h1>🚀 Secure Control Console</h1></div><div class=\"card\"><h3>📂 File Center Matrix</h3><div id=\"files\">Querying storage...</div></div><div class=\"card\"><h3>🛡️ Subnet Watchdog</h3><div id=\"devs\">Mapping airwaves...</div></div><div class=\"card full-width\"><h3>💻 Remote Command Terminal</h3><input id=\"cmd\" placeholder=\"Type command...\" onkeydown=\"if(event.key===\x27Enter\x27)runCmd()\"><button onclick=\"runCmd()\">Execute</button><div class=\"term-box\" id=\"term-out\">Terminal ready. Standby...</div></div></div><script>fetch(\x27/api/files\x27).then(r=>r.json()).then(d=>{document.getElementById(\x27files\x27).innerHTML=d.files.map(f=>\x27<div>📄 \x27+f+\x27 <a href=\"/download/\x27+f+\x27\">[📥 Download]</a></div>\x27).join(\x27\x27)});fetch(\x27/api/watchdog\x27).then(r=>r.json()).then(d=>{document.getElementById(\x27devs\x27).innerHTML=d.devices.length?d.devices.map(v=>\x27<div>📱 \x27+v.ip+\x27 (\x27+v.mac+\x27)</div>\x27).join(\x27\x27):\x27No adjacent nodes mapped yet.\x27});async function runCmd(){const c=document.getElementById(\x27cmd\x27).value;document.getElementById(\x27term-out\x27).innerText=\x27Executing...\x27;const r=await fetch(\x27/api/terminal\x27,{method:\x27POST\x27,headers:{\x27Content-Type\x27:\x27application/json\x27},body:JSON.stringify({command:c})});const s=await r.json();document.getElementById(\x27term-out\x27).innerText=s.output;}</script></body></html>'

@app.route('/')
def home(): return render_template_string(UI) if is_auth() else redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        d = request.get_json()
        if d.get('username') == ADMIN_USER and d.get('password') == ADMIN_PASS:
            r = make_response(jsonify({'status':'success'}), 200)
            r.set_cookie('session_auth', AUTH_TOKEN, httponly=True)
            return r
        return jsonify({'status':'fail'}), 401
    return '<h2>🔒 Unlock Console</h2><form onsubmit=\"event.preventDefault(); fetch(\x27/login\x27,{method:\x27POST\x27,headers:{\x27Content-Type\x27:\x27application/json\x27},body:JSON.stringify({username:document.getElementById(\x27u\x27).value,password:document.getElementById(\x27p\x27).value})}).then(res=>res.ok?window.location.href=\x27/\x27:alert(\x27Invalid\x27))\"><input id=\"u\" placeholder=\"User\"><input type=\"password\" id=\"p\"><button>Access Control</button></form>'

@app.route('/api/files')
def list_files(): return jsonify({'files': sorted(os.listdir(STORAGE_DIR))}) if is_auth() else ('Unauthorized', 401)

@app.route('/api/watchdog')
def get_watchdog(): return jsonify({'devices': watchdog_cache}) if is_auth() else ('Unauthorized', 401)

@app.route('/download/<path:f>')
def download_file(f): return send_from_directory(STORAGE_DIR, f, as_attachment=True) if is_auth() else ('Unauthorized', 401)

@app.route('/api/terminal', methods=['POST'])
def run_terminal():
    if not is_auth(): return jsonify({'output':'Unauthorized'}), 401
    try:
        c = request.get_json().get('command','')
        if any(char in c for char in [';', '&&', '||', '|', '`', '$']):
            return jsonify({'output': 'Security Alert: Command injection chaining blocked!'}), 403
        out = subprocess.check_output(c, shell=True, stderr=subprocess.STDOUT, timeout=10).decode()
        return jsonify({'output': out})
    except Exception as e: 
        return jsonify({'output': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
