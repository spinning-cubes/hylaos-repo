const fs = require('fs');
const path = require('path');

// Directories/files to ignore during traversal
const IGNORE = new Set(['node_modules', '.git', 'manifest.json', '.DS_Store']);

function buildTree(dirPath) {
  const name = path.basename(dirPath);
  const stats = fs.statSync(dirPath);

  if (stats.isDirectory()) {
    const children = fs.readdirSync(dirPath)
      .filter(child => !IGNORE.has(child))
      .map(child => buildTree(path.join(dirPath, child)));

    return {
      name,
      type: 'directory',
      children
    };
  }

  return {
    name,
    type: 'file',
    size: stats.size
  };
}

const targetDir = process.cwd();
const tree = buildTree(targetDir);

fs.writeFileSync(
  path.join(targetDir, 'manifest.json'),
  JSON.stringify(tree, null, 2)
);

console.log('MANIFEST compiled successfully to manifest.json');