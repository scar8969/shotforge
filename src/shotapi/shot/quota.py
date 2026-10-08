def hit(key_id):
    from ..models import ApiKey, db

    k = ApiKey.query.get(key_id)
    if k.used >= k.quota:
        return False
    k.used += 1
    db.session.commit()
    return True
