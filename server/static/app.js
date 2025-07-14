const socket = io();
let selectedClient = null;

socket.on("update", (data) => {
    const tabs = Object.keys(data);
    const tabContainer = document.getElementById("tabs");
    tabContainer.innerHTML = tabs.map(client_id =>
        `<button onclick="showClient('${client_id}')">${client_id}</button>`
    ).join(" ");

    if (!selectedClient && tabs.length > 0) {
        selectedClient = tabs[0];
    }
    renderProcesses(data[selectedClient]);
});

function showClient(client_id) {
    selectedClient = client_id;
}

function renderProcesses(processes) {
    const content = document.getElementById("content");
    content.innerHTML = `
        <table border="1">
            <thead>
                <tr><th>PID</th><th>Name</th><th>CPU %</th><th>MEM MB</th><th>Action</th></tr>
            </thead>
            <tbody>
                ${processes.map(proc => `
                    <tr>
                        <td>${proc.pid}</td>
                        <td>${proc.name}</td>
                        <td>${proc.cpu}</td>
                        <td>${proc.memory_mb}</td>
                        <td><button onclick="killProcess('${proc.pid}')">Kill</button></td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
    `;
}

function killProcess(pid) {
    socket.emit("kill_process", { client_id: selectedClient, pid: pid });
}
