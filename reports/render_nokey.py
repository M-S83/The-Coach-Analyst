# Runs the Match Lens renderer with the evidence-grade legend removed.
# Loads the skill's render.py unmodified from disk and patches only the header key.
import sys, types, os
sys.path.insert(0, "/root/.claude/skills/matchlens-tactical-report/scripts")
SKILL="/root/.claude/skills/matchlens-tactical-report/scripts/render.py"
src=open(SKILL).read()
i=src.index("    hkey=('<div class=\"hkey\">"); j=src.index("\n", src.index("</div>')", i))
src=src[:i]+"    hkey=''\n"+src[j+1:]
m=types.ModuleType("mlrender"); m.__file__=SKILL; m.__name__="mlrender"
sys.modules["mlrender"]=m
exec(compile(src, SKILL, "exec"), m.__dict__)
m.main(sys.argv[1], sys.argv[2], sys.argv[3])
