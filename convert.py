import os
import sys
import json
import xml.etree.ElementTree as ET

if len(sys.argv) < 2:
  print(f"Usage {sys.argv[0]} MUBIN-DIR")
  exit()
else:
  mubin_dir = sys.argv[1]

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
for filename in os.listdir(mubin_dir):
  # no obvious way to list paths
  root = ET.parse(os.path.join(mubin_dir, filename)).getroot()

  for obj in root.findall("./Objs/value"):
    hashid = obj.get("HashId")
    if hashid:
      entry = {"id": hashid, "links": []}
      for link in obj.findall("./LinksToObj/value"):
        hashid = link.get("DestUnitHashId")
        if hashid:
          ltype = link.find("DefinitionName")
          entry["links"].append({
            "id": hashid,
            # bool(ltype) is False, because the Element has no children
            "type": ltype.text if (ltype is not None and ltype.text) else "Unknown"})
      objects.append(entry)
  print(filename)

with open(mubin_dir+".json", "w") as out:
  json.dump(objects, out, indent=2)
