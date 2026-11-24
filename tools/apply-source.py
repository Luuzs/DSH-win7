"""Apply the audited controls at the upstream TypeScript and desktop bundler entry points."""
import argparse
import importlib.util
from pathlib import Path

def replace(path,before,after):
    source=path.read_text(encoding='utf-8')
    if after in source and before not in source:return
    if source.count(before)!=1:raise ValueError(f'Upstream source changed: {path.name} / {before[:65]}')
    path.write_text(source.replace(before,after),encoding='utf-8',newline='\n')

def apply(harness,kit):
    f=kit/'tools/harden-app.py'
    spec=importlib.util.spec_from_file_location('offline_guard',f)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    desktop=harness/'apps/desktop';host=harness/'apps/desktop-host'
    (desktop/'intranet-bootstrap.mjs').write_text(module.NODE_GUARD+"\nimport { app as intranetApp } from 'electron';\n"+module.BROWSER_GUARD.replace('app.','intranetApp.'),encoding='utf-8',newline='\n')
    (host/'intranet-bootstrap.mjs').write_text(module.NODE_GUARD,encoding='utf-8',newline='\n')
    # Both official bundlers support Rolldown outputOptions.banner. It is placed
    # before application initialization in the two binaries shipped to Windows.
    p=desktop/'tsdown.config.ts'
    source=p.read_text()
    if 'intranet-bootstrap.mjs' not in source:
        needle="    entry: ['lib/types/main.js'],"
        replace(p,needle,needle+"\n    outputOptions: { banner: readFileSync(new URL('./intranet-bootstrap.mjs', import.meta.url), 'utf8') },")
    p=host/'tsdown.config.ts'
    if 'intranet-bootstrap.mjs' not in p.read_text():
        replace(p,"import { defineConfig } from 'tsdown'","import { readFileSync } from 'node:fs'\nimport { defineConfig } from 'tsdown'")
        replace(p,"outputOptions: { codeSplitting: false }","outputOptions: { codeSplitting: false, banner: name === 'cli' ? readFileSync(new URL('./intranet-bootstrap.mjs', import.meta.url), 'utf8') : '' }")
    p=desktop/'src/update-coordinator.ts'
    replace(p,"() => app.isPackaged && existsSync(join(process.resourcesPath, 'app-update.yml'))","() => false")
    for unused in ["import { existsSync } from 'node:fs'\n","import { join } from 'node:path'\n"]:
        s=p.read_text(encoding='utf-8');p.write_text(s.replace(unused,''),encoding='utf-8',newline='\n')
    p=harness/'packages/client/product-analytics/src/index.ts'
    replace(p,'return this.active && this.config.enabled.get()','return false')
    p=harness/'packages/bundle/web-app/cordis.patch.yml'
    replace(p,'enabled: true\n        appVersion:','enabled: false\n        appVersion:')
    p=desktop/'scripts/electron-builder-config.mjs'
    replace(p,'const policy = packagesMacOS && unsigned ? undefined : resolveDesktopPolicyEnvironment(env)',
            "const policy = resolvedPlatform === 'win32' || (packagesMacOS && unsigned) ? undefined : resolveDesktopPolicyEnvironment(env)")
    replace(p,'const update = unsigned ? undefined : resolveDesktopAutoUpdateConfig(env, resolvedPlatform, resolvedArch)',
            "const update = resolvedPlatform === 'win32' || unsigned ? undefined : resolveDesktopAutoUpdateConfig(env, resolvedPlatform, resolvedArch)")
    replace(p,"const win7Feed = unsigned && resolvedPlatform === 'win32' ? win7UpdateFeed(env) : undefined",
            "const win7Feed = undefined // Intranet builds have no update feed.")

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--harness',type=Path,default=root/'dsh-win7/deepseek-harness')
    p.add_argument('--kit',type=Path,default=root/'out/kit')
    args=p.parse_args();apply(args.harness,args.kit)
