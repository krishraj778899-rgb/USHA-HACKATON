/* =========================================================
   CARBONFARM - FRONTEND + FLASK BACKEND
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const $ = (selector) => document.querySelector(selector);
    const $$ = (selector) => document.querySelectorAll(selector);

    const API_URL = "/api/assessment";
    const STORAGE_KEY = "carbonFarmAssessment";

    /* =====================================================
       MOBILE NAVIGATION
       ===================================================== */

    const menuBtn = $(".menu-btn");
    const navLinks = $(".nav-links");

    if (menuBtn && navLinks) {
        menuBtn.addEventListener("click", () => {
            navLinks.classList.toggle("active");
            menuBtn.classList.toggle("active");
        });
    }

    $$(".nav-links a").forEach(link => {
        link.addEventListener("click", () => {
            navLinks?.classList.remove("active");
            menuBtn?.classList.remove("active");
        });
    });


    /* =====================================================
       SMOOTH SCROLL
       ===================================================== */

    $$('a[href^="#"]').forEach(link => {

        link.addEventListener("click", function (e) {

            const targetId = this.getAttribute("href");

            if (!targetId || targetId === "#") return;

            const target = $(targetId);

            if (target) {
                e.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });


    /* =====================================================
       ACTIVE NAVIGATION
       ===================================================== */

    const sections = $$("section[id]");
    const navigationLinks = $$(".nav-links a");

    window.addEventListener("scroll", () => {

        let currentSection = "";

        sections.forEach(section => {

            const sectionTop = section.offsetTop - 150;

            if (window.scrollY >= sectionTop) {
                currentSection = section.getAttribute("id");
            }
        });

        navigationLinks.forEach(link => {

            link.classList.remove("active");

            const href = link.getAttribute("href");

            if (href === `#${currentSection}`) {
                link.classList.add("active");
            }
        });
    });


    /* =====================================================
       FORM ELEMENTS
       ===================================================== */

    const assessmentForm = $("#assessmentForm");
    const analysisMessage = $("#analysisMessage");
    const assessmentResult = $("#assessmentResult");

    const farmerName = $("#farmerName");
    const landArea = $("#landArea");
    const mainCrop = $("#mainCrop");
    const practice = $("#practice");
    const documents = $("#documents");


    /* =====================================================
       SHOW MESSAGE
       ===================================================== */

    function showMessage(message, type = "info") {

        if (!analysisMessage) return;

        analysisMessage.textContent = message;

        analysisMessage.className = "analysis-message";

        if (type === "success") {
            analysisMessage.classList.add("success");
        }

        if (type === "error") {
            analysisMessage.classList.add("error");
        }

        if (type === "loading") {
            analysisMessage.classList.add("loading");
        }

        analysisMessage.style.display = "block";
    }


    /* =====================================================
       HIDE MESSAGE
       ===================================================== */

    function hideMessage() {

        if (!analysisMessage) return;

        analysisMessage.style.display = "none";
        analysisMessage.textContent = "";
    }


    /* =====================================================
       RENDER ASSESSMENT RESULT
       ===================================================== */

    function renderResult(data) {

        if (!assessmentResult) return;

        const score = Number(data.score || 0);

        const breakdown = data.breakdown || {};

        const landScore = Number(breakdown.land || 0);
        const cropScore = Number(breakdown.crop || 0);
        const practiceScore = Number(breakdown.practice || 0);
        const documentScore = Number(breakdown.documents || 0);

        /* -----------------------------------------------
           SCORE
           ----------------------------------------------- */

        const resultScore = $("#resultScore");

        if (resultScore) {
            resultScore.textContent = score;
        }


        /* -----------------------------------------------
           SCORE CIRCLE
           ----------------------------------------------- */

        const scoreCircle = $("#scoreCircle");

        if (scoreCircle) {

            scoreCircle.style.background =
                `conic-gradient(
                    #238636 ${score * 3.6}deg,
                    #e8f0e8 ${score * 3.6}deg
                )`;
        }


        /* -----------------------------------------------
           STATUS
           ----------------------------------------------- */

        const resultStatus = $("#resultStatus");

        if (resultStatus) {
            resultStatus.textContent = data.status || "Assessment Complete";
        }


        /* -----------------------------------------------
           SUMMARY
           ----------------------------------------------- */

        const resultSummary = $("#resultSummary");

        if (resultSummary) {
            resultSummary.textContent =
                data.summary || "Assessment completed successfully.";
        }


        /* -----------------------------------------------
           BREAKDOWN TOTAL
           ----------------------------------------------- */

        const breakdownTotal = $("#breakdownTotal");

        if (breakdownTotal) {
            breakdownTotal.textContent = `${score}/100`;
        }


        /* -----------------------------------------------
           LAND SCORE
           ----------------------------------------------- */

        const landScoreElement = $("#landScore");
        const landBar = $("#landBar");

        if (landScoreElement) {
            landScoreElement.textContent = `${landScore}/20`;
        }

        if (landBar) {
            landBar.style.width = `${(landScore / 20) * 100}%`;
        }


        /* -----------------------------------------------
           CROP SCORE
           ----------------------------------------------- */

        const cropScoreElement = $("#cropScore");
        const cropBar = $("#cropBar");

        if (cropScoreElement) {
            cropScoreElement.textContent = `${cropScore}/15`;
        }

        if (cropBar) {
            cropBar.style.width = `${(cropScore / 15) * 100}%`;
        }


        /* -----------------------------------------------
           PRACTICE SCORE
           ----------------------------------------------- */

        const practiceScoreElement = $("#practiceScore");
        const practiceBar = $("#practiceBar");

        if (practiceScoreElement) {
            practiceScoreElement.textContent = `${practiceScore}/30`;
        }

        if (practiceBar) {
            practiceBar.style.width = `${(practiceScore / 30) * 100}%`;
        }


        /* -----------------------------------------------
           DOCUMENT SCORE
           ----------------------------------------------- */

        const documentScoreElement = $("#documentScore");
        const documentBar = $("#documentBar");

        if (documentScoreElement) {
            documentScoreElement.textContent = `${documentScore}/35`;
        }

        if (documentBar) {
            documentBar.style.width = `${(documentScore / 35) * 100}%`;
        }


        /* -----------------------------------------------
           MISSING EVIDENCE
           ----------------------------------------------- */

        const missingEvidence = $("#missingEvidence");

        if (missingEvidence) {

            missingEvidence.innerHTML = "";

            const missing = data.missingEvidence || [];

            if (missing.length === 0) {

                const item = document.createElement("div");

                item.className = "evidence-item evidence-complete";

                item.innerHTML = `
                    <span>✓</span>
                    <span>All required evidence is available.</span>
                `;

                missingEvidence.appendChild(item);

            } else {

                missing.forEach(itemText => {

                    const item = document.createElement("div");

                    item.className = "evidence-item";

                    item.innerHTML = `
                        <span>!</span>
                        <span>${escapeHTML(itemText)}</span>
                    `;

                    missingEvidence.appendChild(item);
                });
            }
        }


        /* -----------------------------------------------
           RECOMMENDATIONS
           ----------------------------------------------- */

        const recommendationsList = $("#recommendationsList");

        if (recommendationsList) {

            recommendationsList.innerHTML = "";

            const recommendations = data.recommendations || [];

            recommendations.forEach((recommendation, index) => {

                const item = document.createElement("div");

                item.className = "recommendation-item";

                item.innerHTML = `
                    <div class="recommendation-icon">
                        ${index + 1}
                    </div>
                    <div>
                        <strong>Recommendation ${index + 1}</strong>
                        <p>${escapeHTML(recommendation)}</p>
                    </div>
                `;

                recommendationsList.appendChild(item);
            });
        }


        /* -----------------------------------------------
           ASSESSMENT ID
           ----------------------------------------------- */

        const assessmentId = data.assessmentId;

        if (assessmentId) {

            let idElement = $("#assessmentId");

            if (!idElement) {

                const resultActions = $(".result-actions");

                if (resultActions) {

                    idElement = document.createElement("p");

                    idElement.id = "assessmentId";

                    idElement.style.marginTop = "10px";
                    idElement.style.fontSize = "13px";
                    idElement.style.opacity = "0.7";

                    resultActions.appendChild(idElement);
                }
            }

            if (idElement) {
                idElement.textContent =
                    `Assessment ID: CF-${String(assessmentId).padStart(5, "0")}`;
            }
        }


        /* -----------------------------------------------
           SHOW RESULT
           ----------------------------------------------- */

        assessmentResult.style.display = "block";

        assessmentResult.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }


    /* =====================================================
       ESCAPE HTML
       ===================================================== */

    function escapeHTML(value) {

        const div = document.createElement("div");

        div.textContent = value ?? "";

        return div.innerHTML;
    }


    /* =====================================================
       SUBMIT ASSESSMENT
       ===================================================== */

    if (assessmentForm) {

        assessmentForm.addEventListener("submit", async (e) => {

            e.preventDefault();

            hideMessage();

            /* ---------------------------------------------
               GET FORM DATA
               --------------------------------------------- */

            const payload = {

                farmerName:
                    farmerName?.value.trim() || "",

                landArea:
                    landArea?.value || "",

                mainCrop:
                    mainCrop?.value || "",

                practice:
                    practice?.value || "",

                documents:
                    documents?.value || ""
            };


            /* ---------------------------------------------
               VALIDATION
               --------------------------------------------- */

            if (!payload.farmerName) {

                showMessage(
                    "Please enter farmer name.",
                    "error"
                );

                farmerName?.focus();

                return;
            }


            if (!payload.landArea || Number(payload.landArea) <= 0) {

                showMessage(
                    "Please enter a valid land area.",
                    "error"
                );

                landArea?.focus();

                return;
            }


            if (!payload.mainCrop) {

                showMessage(
                    "Please select the main crop.",
                    "error"
                );

                mainCrop?.focus();

                return;
            }


            if (!payload.practice) {

                showMessage(
                    "Please select your farming practice.",
                    "error"
                );

                practice?.focus();

                return;
            }


            if (!payload.documents) {

                showMessage(
                    "Please select your document status.",
                    "error"
                );

                documents?.focus();

                return;
            }


            /* ---------------------------------------------
               LOADING
               --------------------------------------------- */

            const submitButton =
                assessmentForm.querySelector("button[type='submit']");

            const originalButtonText =
                submitButton?.textContent || "Assess My Readiness";


            if (submitButton) {

                submitButton.disabled = true;

                submitButton.textContent =
                    "⏳ Calculating...";
            }


            showMessage(
                "Analyzing your farm data...",
                "loading"
            );


            try {

                /* -----------------------------------------
                   SEND DATA TO FLASK
                   ----------------------------------------- */

                const response = await fetch(API_URL, {

                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(payload)
                });


                const result = await response.json();


                /* -----------------------------------------
                   BACKEND ERROR
                   ----------------------------------------- */

                if (!response.ok || !result.success) {

                    throw new Error(
                        result.message ||
                        "Assessment could not be completed."
                    );
                }


                /* -----------------------------------------
                   SAVE RESULT
                   ----------------------------------------- */

                localStorage.setItem(
                    STORAGE_KEY,
                    JSON.stringify(result.assessment)
                );


                /* -----------------------------------------
                   SUCCESS
                   ----------------------------------------- */

                showMessage(
                    "Assessment completed successfully!",
                    "success"
                );


                renderResult(result.assessment);


            } catch (error) {

                console.error(
                    "CarbonFarm Assessment Error:",
                    error
                );

                showMessage(
                    error.message ||
                    "Unable to connect to CarbonFarm server.",
                    "error"
                );

            } finally {

                if (submitButton) {

                    submitButton.disabled = false;

                    submitButton.textContent =
                        originalButtonText;
                }
            }
        });
    }


    /* =====================================================
       RE-ASSESS BUTTON
       ===================================================== */

    const reassessBtn = $("#reassessBtn");

    if (reassessBtn) {

        reassessBtn.addEventListener("click", () => {

            if (assessmentResult) {
                assessmentResult.style.display = "none";
            }

            hideMessage();

            const analysisSection =
                $("#analysis");

            if (analysisSection) {

                analysisSection.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    }


    /* =====================================================
       PRINT RESULT
       ===================================================== */

    const printResultBtn = $("#printResultBtn");

    if (printResultBtn) {

        printResultBtn.addEventListener("click", () => {

            window.print();
        });
    }


    /* =====================================================
       RESTORE LAST RESULT
       ===================================================== */

    function restoreSavedAssessment() {

        try {

            const saved =
                localStorage.getItem(STORAGE_KEY);

            if (!saved) return;

            const data = JSON.parse(saved);

            if (!data) return;


            /* Restore form values */

            if (farmerName && data.farmerName) {
                farmerName.value = data.farmerName;
            }

            if (landArea && data.landArea) {
                landArea.value = data.landArea;
            }

            if (mainCrop && data.mainCrop) {
                mainCrop.value = data.mainCrop;
            }

            if (practice && data.practice) {
                practice.value = data.practice;
            }

            if (documents && data.documents) {
                documents.value = data.documents;
            }

        } catch (error) {

            console.warn(
                "Unable to restore saved assessment:",
                error
            );
        }
    }


    /* =====================================================
       CHECK BACKEND
       ===================================================== */

    async function checkBackend() {

        try {

            const response =
                await fetch("/api/health");

            if (!response.ok) {
                throw new Error("Backend unavailable");
            }

            const data =
                await response.json();

            console.log(
                "🌱 CarbonFarm Backend:",
                data.message
            );

        } catch (error) {

            console.warn(
                "CarbonFarm backend is not connected.",
                error
            );
        }
    }


    /* =====================================================
       INITIALIZE
       ===================================================== */

    restoreSavedAssessment();

    checkBackend();


    /* =====================================================
       HERO START BUTTON
       ===================================================== */

    $$(".primary-btn, .mobile-start-btn").forEach(button => {

        button.addEventListener("click", () => {

            const analysisSection =
                $("#analysis");

            if (analysisSection) {

                setTimeout(() => {

                    analysisSection.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                }, 100);
            }
        });
    });


    console.log(
        "🌱 CarbonFarm frontend initialized successfully."
    );

});