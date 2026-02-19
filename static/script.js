const backendURL = "/analyze";


const fileInput = document.getElementById("vcfFile");
const uploadText = document.getElementById("uploadText");
const uploadBox = document.getElementById("uploadBox");
const loadingOverlay = document.getElementById("loadingOverlay");

fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
        uploadText.textContent = "Selected File: " + fileInput.files[0].name;
        uploadBox.classList.add("active");
    }
});

async function analyze() {

    const file = fileInput.files[0];
    const drug = document.getElementById("drugName").value;

    if (!file || !drug) {
        alert("Upload VCF file and enter drug name.");
        return;
    }

    loadingOverlay.style.display = "flex";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("drug", drug);

    try {
        const response = await fetch(backendURL, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        document.getElementById("resultSection").style.display = "block";
        document.getElementById("jsonOutput").textContent =
            JSON.stringify(data, null, 2);

        if (data.risk_assessment) {

            const risk = data.risk_assessment.risk_label.toLowerCase();
            let className = "unknown";

            if (risk.includes("safe")) className = "safe";
            else if (risk.includes("adjust")) className = "adjust";
            else if (risk.includes("not") || risk.includes("alternative"))
                className = "toxic";

            document.getElementById("riskBadge").innerHTML =
                `<span class="risk-badge ${className}">
                    ${data.risk_assessment.risk_label}
                </span>`;
        }

    } catch (error) {
        alert("Error during analysis.");
    }

    loadingOverlay.style.display = "none";
}

function copyJSON() {
    navigator.clipboard.writeText(
        document.getElementById("jsonOutput").textContent
    );
}

function downloadJSON() {
    const text = document.getElementById("jsonOutput").textContent;
    const blob = new Blob([text], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "pharmaguard_result.json";
    link.click();
}
