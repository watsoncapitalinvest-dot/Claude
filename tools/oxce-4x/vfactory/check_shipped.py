# Every picture gijoe_vehicles.rul names must be shipped: in one of the given mod_update zips or already in John's installed
# mod (a listing of user\mods\GIJoe4x\Resources\VehiclesPrivate). BUILD-1 18:50: a rul naming a file nobody ships stops the
# game at start (FATAL FileRecord::at). Run before every delivery.
# usage: python3 check_shipped.py gijoe_vehicles.rul installed_list.txt zip [zip ...]
import sys, re, zipfile
rul, inst, zips = sys.argv[1], sys.argv[2], sys.argv[3:]
need = sorted(set(re.findall(r'Resources/VehiclesPrivate/[A-Za-z0-9_.]+\.png', open(rul).read())))
have = {l.strip().split('/')[-1] for l in open(inst) if l.strip()}
for z in zips:
    have |= {n.split('/')[-1] for n in zipfile.ZipFile(z).namelist()}
miss = [n for n in need if n.split('/')[-1] not in have]
print(f'{len(need)} named, {len(miss)} not shipped'); [print('MISSING', m) for m in miss]; sys.exit(1 if miss else 0)
