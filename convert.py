import os
import sys
import json
import xml.etree.ElementTree as ET
import struct
import subprocess

def hex_repr(hashid):
  return "0x" + struct.pack(">i", int(hashid)).hex()

def prepare_json(infiles, outfile):
  '''[
    {
      "id":    <hashid>,
      "links": [
        {
          "id":   <hashid>,
          "type": <type>
        },
        ...
      ]
    },
    ...
  ]'''
  objects = []
  for path in infiles:
    root = ET.parse(path).getroot()

    for obj in root.findall("./Objs/value"):
      hashid = obj.get("HashId")
      if hashid:
        hashid = hex_repr(hashid)
        name = obj.find("UnitConfigName")
        name = name.text if (name is not None and name.text) else "Unknown"
        entry = {"id": hashid, "name": name, "links": []}
        for link in obj.findall("./LinksToObj/value"):
          hashid = link.get("DestUnitHashId")
          if hashid:
            hashid = hex_repr(hashid)
            ltype = link.find("DefinitionName")
            entry["links"].append({
              "id": hashid,
              # bool(ltype) is False, because the Element has no children
              "type": ltype.text if (ltype is not None and ltype.text) else "Unknown"})
        objects.append(entry)
    print(path)

  with open(outfile, "w") as out:
    json.dump(objects, out, indent=2)

def parse_hashid(s):
  if s.startswith("0x"):
    return s
  elif -(2**32) <= int(s) <= (2**32-1):
    return hex_repr(s)

def filter_graph(infile, hashid, outfile):
  with open(infile, "r") as inf:
    objects = json.load(inf)

  graph = []
  hashids = [hashid]
  i = 0
  while i < len(hashids):
    hashid = hashids[i]
    i += 1
    print(f"Searching for obj #{i}/{len(hashids)}", end='\r')
    for obj in objects:
      if str(obj).find(hashid) != -1:
        if obj["id"] not in hashids:
          hashids.append(obj["id"])
        for link in obj["links"]:
          hid = link["id"]
          if hid not in hashids:
            hashids.append(hid)
  for obj in objects:
    if obj["id"] in hashids:
      graph.append(obj)

  with open(outfile, "w") as out:
    json.dump(graph, out, indent=2)

def to_dot(infile, dotfile):
  with open(infile, "r") as inf:
    objects = json.load(inf)

  graph = []
  for obj in objects:
    graph.append(f'_{obj["id"]} [shape=record label=\"{{{obj["name"]}|{obj["id"]}}}\"]')

    for link in obj["links"]:
      graph.append(f'_{obj["id"]} -> _{link["id"]} [label=\"{link["type"]}\"]')

  with open(dotfile, "w") as out:
    out.write("digraph {\n  ")
    out.write("\n  ".join(graph))
    out.write("\n}")

def main():
  if len(sys.argv) < 3:
    print(f"Usage {sys.argv[0]} MUBIN-DIR|DUNGEON HASHID")
    exit()

  source = sys.argv[1]
  if os.path.isdir(source):
    files = [os.path.join(source, file) for file in os.listdir(source)]
  else:
    if source in ["Fire", "Water", "Electric", "Wind"]:
      files = [f"mubin_dungeon/Remains{source}_Static.xml", f"mubin_dungeon/Remains{source}_Dynamic.xml"]
      if source == "Water":
        files.append("mubin_dungeon/Set_Dungeon_RemainsWater.xml")
    elif source == "Final":
      files = ["mubin_dungeon/FinalTrial_Static.xml", "mubin_dungeon/FinalTrial_Dynamic.xml", "mubin_dungeon/Set_DLC_FinalTrial_FirePillar_A.xml", "mubin_dungeon/Set_DLC_FinalTrial_ShutterFence_A.xml", "mubin_dungeon/Set_FinalTrial_DoorBoss.xml", "mubin_dungeon/Set_FinalTrial_Lift.xml", "mubin_dungeon/Set_FinalTrial_OutWall.xml", "mubin_dungeon/Set_FinalTrial_SliderRod.xml"]
    elif source.isnumeric():
      files = [f"mubin_dungeon/Dungeon{source}_Static.xml", f"mubin_dungeon/Dungeon{source}_Dynamic.xml"]
    else:
      print(f"Invalid dungeon {source}")
      exit()

  mubin_json = source+".json"

  if not os.path.isfile(mubin_json):
    prepare_json(files, mubin_json)

  hashid = parse_hashid(sys.argv[2])
  if not hashid:
    print(f"Invalid HashId {sys.argv[2]}")
    exit()

  mubin_hashid_json = f"{source}-{hashid}.json"

  if not os.path.isfile(mubin_hashid_json):
    filter_graph(mubin_json, hashid, mubin_hashid_json)

  dotfile = f"{source}-{hashid}.dot"
  to_dot(mubin_hashid_json, dotfile)

  subprocess.Popen(["xdot", dotfile]) # disgusting

if __name__ == '__main__':
  main()