# Launch occlusion for firing clips (John 20:21 and 21:29: "they appear in the pod ... this happens often").
# A flying missile starts with its nose on the mounted one, so for its first frames part of it is still inside the pod / rack.
# The vehicle picture with the missile still mounted shows exactly which of its pixels the pod hides: wherever the flying
# missile's launch footprint covers vehicle pixels that did NOT change when the missile left (loaded state vs next state),
# something in front of the tube is drawn there (the pod's face, the rack's frame). Those pixels stay in front of the missile
# for the rest of its flight; everywhere else it is drawn over the vehicle as before.
# occluder(before, after, missile, (px, py)) -> L mask (canvas size, 255 = vehicle in front); before/after are the vehicle
# composited alone on transparent canvases of the clip's size.
from PIL import Image, ImageChops, ImageFilter
def occluder(before, after, missile, pos):
    W, H = before.size
    foot = Image.new('L', (W, H), 0); foot.paste(missile.getchannel('A').point(lambda v: 255 if v > 32 else 0), pos)
    d = ImageChops.difference(before, after).convert('L').point(lambda v: 255 if v > 12 else 0).filter(ImageFilter.MaxFilter(3))
    solid = after.getchannel('A').point(lambda v: 255 if v > 128 else 0)
    return ImageChops.multiply(ImageChops.multiply(foot, ImageChops.invert(d)), solid)
def draw(canvas, missile, pos, mask, vehicle_after):
    """Missile at pos over canvas, then the vehicle's pixels under mask put back in front of it."""
    canvas.alpha_composite(missile, pos)
    if mask is not None: canvas.paste(vehicle_after, (0, 0), ImageChops.multiply(mask, vehicle_after.getchannel('A')))
