import os

files = [
    r'd:\practice\AIML-vlab\frontend\src\components\Navbar\Navbar.js',
    r'd:\practice\AIML-vlab\frontend\src\components\LandingPage\LandingPage.js',
    r'd:\practice\AIML-vlab\frontend\src\components\Home\Home.js',
    r'd:\practice\AIML-vlab\frontend\src\components\Sidebar\Sidebar.js'
]

for fpath in files:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('🧪', '🧠')
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

print('Icons swapped to 🧠 successfully.')
