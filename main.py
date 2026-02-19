from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import cohere
import os

app = FastAPI()

# Allow all origins (safe for hackathon demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# Initialize Cohere client
co = cohere.Client(os.getenv("COHERE_API_KEY"))


def parse_vcf(contents: str):
    """
    Basic mock VCF parsing.
    Extracts rsIDs for demo purposes.
    """
    genes = ["CYP2D6"]
    rsids = []
    star_alleles = ["*1/*4"]

    for line in contents.splitlines():
        if line.startswith("rs"):
            rsids.append(line.split()[0])

    return {
        "patient_id": "PATIENT_" + str(abs(hash(contents)) % 100000),
        "genes": genes,
        "rsids": rsids[:3] if rsids else ["rs123456"],
        "star_alleles": star_alleles
    }


def build_prompt(parsed_data, drug):
    return f"""
Analyze pharmacogenomic risk for the drug: {drug}

Patient ID: {parsed_data['patient_id']}
Genes: {parsed_data['genes']}
Variants: {parsed_data['rsids']}
Star Alleles: {parsed_data['star_alleles']}

Return ONLY valid JSON in this exact format:

{{
  "patient_id": "{parsed_data['patient_id']}",
  "drug": "{drug}",
  "timestamp": "{datetime.utcnow().isoformat()}",
  "risk_assessment": {{
    "risk_label": "Safe|Not Safe|Adjust Dosage|Alternative Recommended|Unknown",
    "overall_decision": "Safe to Prescribe|Avoid|Use Alternative Drug|Dose Adjustment Required",
    "clinical_risk_summary": "Short explanation",
    "confidence_score": 0.85,
    "severity": "none|low|moderate|high|critical"
  }},
  "pharmacogenomic_profile": {{
    "primary_gene": "GENE_SYMBOL",
    "diplotype": "*X/*Y",
    "phenotype": "PM|IM|NM|RM|URM|Unknown",
    "detected_variants": [
      {{
        "rsid": "rsXXXX"
      }}
    ]
  }},
  "clinical_recommendation": {{
    "recommendation_summary": "Actionable recommendation",
    "alternative_drug_suggestion": "If needed",
    "cpic_guideline_reference": "Guideline reference"
  }},
  "llm_generated_explanation": {{
    "summary": "Biological explanation"
  }},
  "quality_metrics": {{
    "vcf_parsing_success": true,
    "genes_detected": true
  }}
}}

Do NOT include markdown.
Return only raw JSON.
"""


def call_cohere(prompt):
    response = co.chat(
        model="command-a-03-2025",
        message=prompt,
        temperature=0.1
    )

    raw_text = response.text.strip()

    try:
        start = raw_text.index("{")
        end = raw_text.rindex("}") + 1
        return raw_text[start:end]
    except:
        return JSONResponse(
            status_code=500,
            content={"error": "Model returned invalid JSON"}
        )

<-- return dict directly
@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    drug: str = Form(...)
):
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8", errors="ignore")

        parsed_data = parse_vcf(decoded)
        prompt = build_prompt(parsed_data, drug)
        result = call_cohere(prompt)

        return result

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
