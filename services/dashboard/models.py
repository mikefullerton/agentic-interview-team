"""Read-only data access for the dev-team database."""

from . import db


def list_projects(conn):
    return [
        db.dict_from_row(r)
        for r in conn.execute(
            "SELECT * FROM projects ORDER BY name"
        ).fetchall()
    ]


def list_sessions(conn, project_id=None, workflow=None, status=None):
    sql = """
        SELECT wr.*, p.name as project_name,
            (SELECT COUNT(*) FROM session_state ar
             WHERE ar.session_id = wr.id) as agent_total,
            (SELECT COUNT(*) FROM session_state ar
             WHERE ar.session_id = wr.id AND ar.status = 'completed') as agents_done,
            (SELECT COUNT(*) FROM session_state ar
             WHERE ar.session_id = wr.id AND ar.status = 'running') as agents_active,
            (SELECT COUNT(*) FROM session_state ar
             WHERE ar.session_id = wr.id AND ar.status = 'failed') as agents_failed
        FROM sessions wr
        JOIN projects p ON wr.project_id = p.id
        WHERE 1=1
    """
    params = []
    if project_id:
        sql += " AND wr.project_id = ?"
        params.append(project_id)
    if workflow:
        sql += " AND wr.workflow = ?"
        params.append(workflow)
    if status:
        sql += " AND wr.status = ?"
        params.append(status)
    sql += " ORDER BY wr.started DESC"
    return [db.dict_from_row(r) for r in conn.execute(sql, params).fetchall()]


def get_session(conn, run_id):
    row = conn.execute(
        """SELECT wr.*, p.name as project_name
           FROM sessions wr
           JOIN projects p ON wr.project_id = p.id
           WHERE wr.id = ?""",
        (run_id,),
    ).fetchone()
    if not row:
        return None
    result = db.dict_from_row(row)
    result["agents"] = list_state_transitions(conn, run_id)
    result["findings"] = list_findings_for_session(conn, run_id)
    result["specialist_assignments"] = list_specialist_assignments(conn, run_id)
    return result


def list_state_transitions(conn, session_id):
    return [
        db.dict_from_row(r)
        for r in conn.execute(
            "SELECT * FROM session_state WHERE session_id = ? ORDER BY started ASC",
            (session_id,),
        ).fetchall()
    ]


def list_messages(conn, session_id, since_id=0):
    return [
        db.dict_from_row(r)
        for r in conn.execute(
            """SELECT * FROM messages
               WHERE session_id = ? AND id > ?
               ORDER BY id ASC""",
            (session_id, since_id),
        ).fetchall()
    ]


def list_findings_for_session(conn, session_id):
    return [
        db.dict_from_row(r)
        for r in conn.execute(
            """SELECT f.*, ar.agent_type, ar.specialist_domain as agent_specialist
               FROM findings f
               JOIN session_state ar ON f.session_state_id = ar.id
               WHERE ar.session_id = ?
               ORDER BY f.created ASC""",
            (session_id,),
        ).fetchall()
    ]


def list_specialist_assignments(conn, session_id):
    return [
        db.dict_from_row(r)
        for r in conn.execute(
            """SELECT * FROM specialist_assignments
               WHERE session_id = ?
               ORDER BY tier ASC, specialist ASC""",
            (session_id,),
        ).fetchall()
    ]
