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
