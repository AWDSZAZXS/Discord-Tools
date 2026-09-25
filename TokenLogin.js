// F12 후 콘솔창에 붙여넣으세요
javascript:(function() {
    let token = prompt("디스코드 토큰을 입력하세요:");
    if (!token) return;
    setInterval(() => {
        document.body.appendChild(document.createElement `iframe`).contentWindow.localStorage.token = `"${token}"`;
    }, 50);
    setTimeout(() => {
        location.reload();
    }, 500);
})();
