from flask_app import app
from models import Student

with app.app_context():
    s = Student.query.filter(Student.parent_id != None).first()
    if not s:
        print('NO_STUDENT_WITH_PARENT')
        exit(0)
    print('FOUND_STUDENT', s.id, 'parent', s.parent_id)
    parent_id = s.parent_id
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = parent_id
        sess['role'] = 'parent'
    resp = client.get(f'/parent/child/{s.id}/export?fmt=doc')
    print('STATUS', resp.status_code)
    print('CONTENT-TYPE', resp.headers.get('Content-Type'))
    data = resp.get_data()
    print('LENGTH', len(data))
    print('PREFIX')
    print(data[:1000].decode('utf-8', errors='ignore'))
