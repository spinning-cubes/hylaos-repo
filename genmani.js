const fs = require('fs');
const path = require('path');

// Directories/files to ignore during traversal
const IGNORE = new Set(['node_modules', '.git', 'manifest.json', '.DS_Store']);

function getFileSize(filePath, stats) {
  // LFS pointer files are small text files under 1KB
  if (stats.size > 0 && stats.size < 1024) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      if (content.startsWith('version https://git-lfs.github.com/spec/v1')) {
        const sizeMatch = content.match(/^size\s+(\d+)/m);
        if (sizeMatch) {
          return parseInt(sizeMatch[1], 10);
        }
      }
    } catch {
      // Fall back to standard disk size if reading fails
    }
  }
  return stats.size;
}

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
    size: getFileSize(dirPath, stats)
  };
}

const targetDir = process.cwd();
const tree = buildTree(targetDir);

fs.writeFileSync(
  path.join(targetDir, 'manifest.json'),
  JSON.stringify(tree, null, 2)
);

console.log('MANIFEST compiled successfully to manifest.json');