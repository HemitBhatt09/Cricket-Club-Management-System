// ==========================
// 🎥 VIDEO INTRO CONTROL
// ==========================
document.addEventListener("DOMContentLoaded", function () {

    const video = document.getElementById("introVideo");

    // If video exists, wait for it to end
    if (video) {
        video.onended = function () {
            const intro = document.getElementById("videoIntro");
            const main = document.getElementById("mainContent");

            if (intro) intro.style.display = "none";
            if (main) main.style.display = "flex";
                    setTimeout(() => {
                    main.classList.add("show");
                    }, 50);
        };
    }

});


// ==========================
// 🔄 FLIP CARD FUNCTION
// ==========================
function flipCard() {
    const card = document.getElementById("flipCard");
    if (card) {
        card.classList.toggle("flipped");
    }
}


// ==========================
// 📝 SIGNUP FUNCTION
// ==========================
function signup() {

    const name = document.getElementById("name").value;
    const mobile = document.getElementById("mobile").value;
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;

    if (!name || !mobile || !password) {
        alert("Please fill all fields");
        return;
    }

    fetch("/signup", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            mobile_no: mobile,
            password: password,
            role: role
        })
    })
    .then(res => res.json())
    .then(data => {

        if (data.message) {
            alert("Signup Successful ✅");

            // Flip back to login after signup
            flipCard();
        } else {
            alert(data.error || "Signup failed");
        }

    })
    .catch(err => {
        console.error(err);
        alert("Error connecting to server");
    });
}


// ==========================
// 🔐 LOGIN FUNCTION
// ==========================
function login() {

    const name = document.getElementById("loginName").value;
    const mobile = document.getElementById("loginMobile").value;
    const password = document.getElementById("loginPassword").value;

    if (!name || !mobile || !password) {
        alert("Please fill all fields");
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            mobile_no: mobile,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {

        if (data.message === "Login successful") {
            alert("Login Successful ✅");

            // 🔥 FUTURE: redirect to dashboard
            window.location.href = "/dashboard";

        } else {
            alert("Invalid Credentials ❌");
        }

    })
    .catch(err => {
        console.error(err);
        alert("Error connecting to server");
    });
}