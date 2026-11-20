const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '../..');
const presets = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = ['state.js', 'render/mesh.js', 'scenes/device.js']
  .map(file => fs.readFileSync(path.join(root, 'src', file), 'utf8')).join('\n');

const extract = `
class AssetMesh extends DeviceMesh {
  constructor() {
    super();
    this.groups = [];
  }

  group(name) {
    this.groups.push({name, offset: this.indices.length});
  }
}

const defaults = {...state};
const meshes = presets.map(preset => {
  Object.assign(state, defaults, preset);
  const mesh = new AssetMesh();
  sampleGround(mesh, state.soilCutaway);
  deviceBuilders[state.phase](mesh);
  return {vertices: mesh.vertices, indices: mesh.indices, groups: mesh.groups};
});
({palette: metal, meshes});
`;

process.stdout.write(JSON.stringify(vm.runInNewContext(source + '\n' + extract, {presets})));
