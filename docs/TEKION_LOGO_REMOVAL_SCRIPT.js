/**
 * Save Authentication Cookies - Run this in browser console
 *
 * USAGE:
 * 1. Login to https://preprodapp.tekioncloud.com manually
 * 2. Open browser console (F12) on any preprod page
 * 3. Paste this script and press Enter
 * 4. Copy the JSON output
 * 5. Save it to auth_state.json in your project root
 * 6. Now the backend can authenticate!
 */

(async function() {
    console.log('🔐 ===============================================');
    console.log('🔐 Extracting Authentication State...');
    console.log('🔐 ===============================================');

    // Step 1: Get all cookies
    console.log('📋 Step 1: Extracting cookies...');
    const cookies = document.cookie.split(';').map(cookie => {
        const [name, ...valueParts] = cookie.trim().split('=');
        return {
            name: name,
            value: valueParts.join('='),
            domain: '.tekioncloud.com',
            path: '/'
        };
    });
    console.log(`✅ Found ${cookies.length} cookies`);

    // Step 2: Get localStorage
    console.log('📋 Step 2: Extracting localStorage...');
    const localStorageItems = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        localStorageItems.push({
            name: key,
            value: localStorage.getItem(key)
        });
    }
    console.log(`✅ Found ${localStorageItems.length} localStorage items`);

    // Step 3: Create auth_state.json structure
    console.log('📋 Step 3: Creating auth_state.json structure...');
    const authState = {
        cookies: cookies,
        origins: [
            {
                origin: window.location.origin,
                localStorage: localStorageItems
            }
        ]
    };

    // Step 4: Output the JSON
    console.log('\n✅ ===============================================');
    console.log('✅ Auth State Extracted!');
    console.log('✅ ===============================================\n');
    console.log('📋 COPY THE JSON BELOW AND SAVE TO: auth_state.json');
    console.log('📋 ===============================================\n');
    console.log(JSON.stringify(authState, null, 2));
    console.log('\n📋 ===============================================');
    console.log('📋 After saving, run the Tekion Logo Removal from the UI!');
    console.log('📋 ===============================================\n');

})();
