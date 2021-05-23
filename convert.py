import os
import sys
import json
import xml.etree.ElementTree as ET
import struct

def hex_repr(hashid):
  return "0x" + struct.pack(">i", int(hashid)).hex()

def prepare_json(indir, outfile):
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
  for filename in os.listdir(indir):
    # no obvious way to list paths
    root = ET.parse(os.path.join(indir, filename)).getroot()

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
    print(filename)

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
  count = 0
  for hashid in hashids:
    print(f"Searching for obj #{count}/{len(hashids)}", end='\r')
    count += 1
    for obj in objects:
      if str(obj).find(hashid) != -1:
        graph.append(obj)
        for link in obj["links"]:
          hid = link["id"]
          if hid not in hashids:
            hashids.append(link["id"])

  with open(outfile, "w") as out:
    json.dump(graph, out, indent=2)

def main():
  if len(sys.argv) < 3:
    print(f"Usage {sys.argv[0]} MUBIN-DIR HASHID")
    exit()

  mubin_dir  = sys.argv[1]
  mubin_json = mubin_dir+".json"

  if not os.path.isfile(mubin_json):
    prepare_json(mubin_dir, mubin_json)

  hashid = parse_hashid(sys.argv[2])
  if not hashid:
    print(f"Invalid HashId {sys.argv[2]}")
    exit()

  mubin_hashid_json = f"{mubin_dir}-{hashid}.json"

  if not os.path.isfile(mubin_hashid_json):
    filter_graph(mubin_json, hashid, mubin_hashid_json)

if __name__ == '__main__':
  main()