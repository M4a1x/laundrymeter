const connection = new signalR.HubConnectionBuilder()
    .withUrl("/datahub")
    .build();

connection.on("DisplayData", (emeter) => {
    //const msg = message.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    em = JSON.parse(emeter);
    document.getElementById("power").textContent = em.Power;
    document.getElementById("total_power").textContent = em.TotalPower;
    document.getElementById("current").textContent = em.Current;
    document.getElementById("voltage").textContent = em.Voltage;
});

connection.start().catch(err => console.error(err.toString()));

document.getElementById("sendButton").addEventListener("click", event => {
    const user = document.getElementById("userInput").value;
    const message = document.getElementById("messageInput").value;
    connection.invoke("SendMessage", user, message).catch(err => console.error(err.toString()));
    event.preventDefault();
});
