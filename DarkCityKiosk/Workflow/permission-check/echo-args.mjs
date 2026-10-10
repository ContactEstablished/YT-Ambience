// Permission-preflight stand-in for ue-guard.mjs: records its arguments and touches nothing else.
// It lets the guard rules' "* render ..." wildcard shape be exercised without invoking the guard.
import fs from 'node:fs';

const args = process.argv.slice(2);
fs.appendFileSync(new URL('./echo-args.log', import.meta.url), JSON.stringify({ at: new Date().toISOString(), args }) + '\n');
console.log('echo-args', JSON.stringify(args));
