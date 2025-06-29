/**
 * @type {import('electron-builder').Configuration}
 * @see https://www.electron.build/configuration/configuration
 */
module.exports = {
  appId: 'com.jarvis.electron',
  productName: 'Jarvis',
  copyright: 'Copyright © 2024 Jarvis Team',
  asar: true,
  
  // Directories
  directories: {
    output: 'release/${version}',
    buildResources: 'build'
  },
  
  // Files to include
  files: [
    'dist/**/*',
    'node_modules/**/*',
    'package.json'
  ],
  
  // Publish configuration
  publish: null,
  
  // macOS configuration
  mac: {
    category: 'public.app-category.productivity',
    icon: 'build/icon.icns',
    hardenedRuntime: true,
    gatekeeperAssess: false,
    entitlements: 'build/entitlements.mac.plist',
    entitlementsInherit: 'build/entitlements.mac.plist',
    target: [
      {
        target: 'dmg',
        arch: ['x64', 'arm64']
      },
      {
        target: 'zip',
        arch: ['x64', 'arm64']
      }
    ]
  },
  
  // macOS DMG configuration
  dmg: {
    icon: 'build/icon.icns',
    iconSize: 100,
    contents: [
      {
        x: 380,
        y: 280,
        type: 'link',
        path: '/Applications'
      },
      {
        x: 110,
        y: 280,
        type: 'file'
      }
    ],
    window: {
      width: 540,
      height: 380
    }
  },
  
  // Windows configuration
  win: {
    icon: 'build/icon.ico',
    publisherName: 'Jarvis Team',
    target: [
      {
        target: 'nsis',
        arch: ['x64']
      },
      {
        target: 'portable',
        arch: ['x64']
      }
    ]
  },
  
  // Windows NSIS installer configuration
  nsis: {
    oneClick: false,
    perMachine: false,
    allowToChangeInstallationDirectory: true,
    deleteAppDataOnUninstall: false,
    createDesktopShortcut: true,
    createStartMenuShortcut: true
  },
  
  // Linux configuration
  linux: {
    icon: 'build/icons/',
    category: 'Office',
    target: [
      {
        target: 'AppImage',
        arch: ['x64']
      },
      {
        target: 'deb',
        arch: ['x64']
      },
      {
        target: 'rpm',
        arch: ['x64']
      }
    ]
  },
  
  // AppImage configuration
  appImage: {
    license: 'LICENSE'
  },
  
  // Debian package configuration
  deb: {
    depends: ['gconf2', 'gconf-service', 'libnotify4', 'libappindicator1', 'libxtst6', 'libnss3']
  },
  
  // Snap configuration (optional)
  snap: {
    grade: 'stable',
    confinement: 'strict'
  }
}