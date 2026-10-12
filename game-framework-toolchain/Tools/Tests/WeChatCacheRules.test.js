// Run with Node.js; checks the exact policy injected into the exported client.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const policy = fs.readFileSync(path.join(__dirname, '../../Templates/GameFramework/ProjectFiles/Assets/Editor/WeChatResourceCache.js.txt'), 'utf8');
const root = 'https://cdn.example.test/game';
const version = '20261009T010203004Z';
const bundle = `${version}/bundles/Login/code_0123456789abcdef0123456789abcdef.bundle`;
const catalog = `${version}/releases/${version}/catalog.json`;
let platform = 'android';
const context = {
    unityNamespace: {},
    GameGlobal: { managerConfig: { DATA_CDN: root } },
    wx: { getSystemInfoSync: () => ({ platform }) }
};
vm.runInNewContext(policy, context);
const cacheable = context.unityNamespace.isCacheableFile;
const cases = [
    [bundle, true],
    [catalog, true],
    [catalog + '?v=1', true],
    ['bootstrap.json', false],
    [`${version}/current.json`, false],
    [`${version}/releases/${version}/manifest.json`, false],
    [`${version}/releases/${version}/settings.json`, false],
    [`${version}/releases/${version}/catalog.hash`, false],
    [`${version}/bundles/code.bundle`, false],
    [`${version}/bundles/../${bundle}`, false]
];
for (const [relative, expected] of cases) {
    assert.strictEqual(cacheable(`${root}/${relative}`), expected, relative);
}
assert.strictEqual(cacheable(`https://other.example.test/game/${bundle}`), false);
assert.strictEqual(cacheable(`${root}-other/${bundle}`), false);
assert.strictEqual(cacheable(null), false);
platform = 'ios';
assert.strictEqual(cacheable(`${root}/${bundle}`), true);
platform = 'devtools';
assert.strictEqual(cacheable(`${root}/${bundle}`), false);
console.log('Passed 15 WeChat cache policy checks.');
