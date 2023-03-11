let currentTime = Math.floor(Date.now() / 1000);
let tokenExpiration = pm.collectionVariables.get("token_expiration");
if ((tokenExpiration && tokenExpiration <= currentTime) || tokenExpiration === undefined) {
    let refresh_token = pm.collectionVariables.get("refresh");
    if (refresh_token) {
        console.log("REFRESHING TOKEN")
        const postRequest = {
            url: `${pm.variables.get("base_url")}/auth/refresh`,
            method: 'POST',
            header: {
                "Content-Type": "application/json"
            },
            body: {
                mode: 'raw',
                raw: JSON.stringify({
                    "refresh_token": refresh_token
                })
            }
        }
        pm.sendRequest(postRequest, function (err, res) {
            var responseJson = res.json();
            if (res.code == 200) {
                pm.collectionVariables.set('token', responseJson['access_token']);
                pm.collectionVariables.set('refresh', responseJson['refresh_token']);

                let expires = currentTime + (responseJson["expiry_min"] * 60)
                pm.collectionVariables.set('token_expiration', expires);
            } else {
                console.log({ "error": err, "response": res });
            }
        });
        return
    };

    console.log("FETCHING NEW TOKEN")
    const postRequest = {
        url: `${pm.variables.get("base_url")}/auth/token`,
        method: 'POST',
        timeout: 0,
        header: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: {
            mode: 'urlencoded',
            urlencoded: [
                { key: "username", value: pm.variables.get("username") },
                { key: "password", value: pm.variables.get("password") },
                { key: "scope", value: pm.variables.get("scope") },
            ]
        }
    };
    pm.sendRequest(postRequest, function (err, res) {
        var responseJson = res.json();
        if (res.code == 200) {
            pm.collectionVariables.set('token', responseJson['access_token']);
            pm.collectionVariables.set('refresh', responseJson['refresh_token']);

            let expires = currentTime + (responseJson["expiry_min"] * 60)
            pm.collectionVariables.set('token_expiration', expires);
        } else {
            console.log({ "error": err, "response": res });
        }
    });
    return
}
console.log("USING CACHED TOKEN")
