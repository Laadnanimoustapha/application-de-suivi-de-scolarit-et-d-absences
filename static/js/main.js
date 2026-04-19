// Basic API Prototype

async function login(role, identifier, password) {
  
    const payload = role === 'admin' ? { username: identifier, password } : { email: identifier, password };
    
    const res = await fetch(`/login/${role}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    
    const data = await res.json();
    
    if (data.statu === "login successfully") {
        const pages = { etudiant: "eleve", professeur: "prof", admin: "admin" };
        window.location.href = `../templates/dashboard_${pages[role]}.html`;
    } else {
        alert("Login Failed: " + data.statu);
    }
}

// Quick server check
fetch("/").then(r => r.json()).then(console.log).catch(console.error);
