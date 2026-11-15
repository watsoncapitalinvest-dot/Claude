"""Attachment slots on the named Joes' signature weapons (STORY's BRIEF_FOR_ROSTER_Attachments, 15 Nov; ATTACHMENTS_DESIGN_v2).
Six slots: optic, under-barrel, muzzle, magazine, side, stock. A gun fits 3 at most, whatever its slots.
SLOTS: the slots each armory gun has. NOTE: the 11 Nov record note ("attachments") read into v2's names:
  items = v2 attachments the note names (a choice at the Armory, not a free upgrade);
  built = things the note lists that are part of the weapon or its ammo, not attachments (no slot)."""
SLOTS = {
 'W_RIFLE_J':  ['optic', 'under-barrel', 'muzzle', 'magazine', 'side', 'stock'],   # M-16
 'W_CARBINE':  ['optic', 'under-barrel', 'muzzle', 'magazine', 'side', 'stock'],   # XM-16
 'W_SMG':      ['optic', 'muzzle', 'magazine', 'side', 'stock'],                   # Uzi, M-32, XF-7: too short for under-barrel kit
 'W_PISTOL':   ['muzzle', 'magazine', 'side'],                                     # pistol suppressor, pistol extended mag, laser sight
 'W_LMG':      ['optic', 'under-barrel', 'muzzle', 'magazine'],                    # M-60: bipod, belt box
 'W_HMG':      ['optic', 'muzzle', 'magazine'],                                    # .50 on its tripod
 'W_LASER_R':  ['optic', 'muzzle', 'magazine'],                                    # brief rule 2: targeting computer / thermal, beam focuser, power cell
 'W_ROCKET':   ['optic'],                                                          # bazooka: its optical sight
 'W_CROSSBOW': ['optic', 'side'],                                                  # already silent: no muzzle
}
NONE = {'W_MORTAR', 'W_FLARE', 'W_HARPOON', 'W_SWORD', 'W_NUNCHAKU'}               # no slots
ITEM = {  # 11 Nov word -> (v2 attachment, slot)
 'scope': ('4x scope', 'optic'), 'optical sight': ('4x scope', 'optic'), 'red dot': ('red dot', 'optic'),
 'under-barrel grenade launcher': ('M203 grenade launcher', 'under-barrel'), 'bipod': ('bipod', 'under-barrel'),
 'bayonet': ('bayonet', 'muzzle'), 'suppressor': ('suppressor', 'muzzle'),
 'folding stock': ('adjustable stock', 'stock'), 'weapon light': ('weapon light', 'side'), 'laser sight': ('laser sight', 'side'),
 'extended magazine': ('extended mag', 'magazine'), 'ammo box': ('drum', 'magazine'), 'ammo belt': ('drum', 'magazine'),
}
ENERGY = {'scope': ('targeting computer', 'optic'), 'extended battery': ('power cell', 'magazine')}
BUILT = {'tripod', 'tripod (must deploy)', 'baseplate', 'smoke rounds', 'extra rockets', 'extra spears', 'explosive bolts'}
def slots_for(weapon):
    """weapon: the record's weapon dict (name, armory, attachments). Returns {armory: {slots, items, built}}."""
    out = {}; note = (weapon.get('attachments') or '').strip()
    note = note.split(':', 1)[1] if note.lower().startswith('uzi:') else note
    words = [x.strip().lower() for x in note.split(',') if x.strip() and x.strip() not in ('-', 'none')]
    for i, a in enumerate(weapon.get('armory') or []):
        if not a or a in NONE or a not in SLOTS:
            out[a] = {'slots': [], 'items': [], 'built': sorted(w for w in words if w in BUILT) if a in NONE else []}; continue
        table = ENERGY if a == 'W_LASER_R' else ITEM; items, built = [], []
        for w in (words if i == 0 else []):                                   # the note is about the first (signature) gun
            if w in table and table[w][1] in SLOTS[a]: items.append(table[w][0])
            elif w in BUILT: built.append(w)
        out[a] = {'slots': SLOTS[a], 'items': items, 'built': built}
    # melee/none guns carry nothing; keep one entry per gun with slots or built parts only
    return {a: v for a, v in out.items() if v['slots'] or v['built']}
