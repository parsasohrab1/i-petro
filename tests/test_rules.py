from server import rules


def _u(role, uid="u1"):
    return {"id": uid, "role": role}


def test_market_and_patentops_are_admin_write():
    for top in ("market", "patentops", "settings"):
        p = f"{top}/data"
        assert rules.can_write(_u("admin"), p) and rules.can_write(_u("owner"), p)
        assert not rules.can_write(_u("member"), p)
        assert rules.can_read(_u("member"), p)


def test_member_collections_stay_open():
    for p in ("tracking/tn_1", "mailreq/t__en", "phonebook/x", "tasksdeleted/t1", "artedits/a"):
        assert rules.can_write(_u("member"), p)


def test_activity_log_is_private_to_member_and_owner():
    p = "activity/u1/days/2026-01-01"
    assert rules.can_write(_u("member", "u1"), p) and not rules.can_write(_u("member", "u2"), p)
    assert not rules.can_write(_u("owner", "o"), p)
    assert rules.can_read(_u("member", "u1"), p) and rules.can_read(_u("owner", "o"), p)
    assert not rules.can_read(_u("member", "u2"), p) and not rules.can_read(_u("admin", "a"), p)
