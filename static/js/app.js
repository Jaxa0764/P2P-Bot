// ==========================================================================
// P2P Crypto Exchange Frontend Logic
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // Application State
    // -------------------------------------------------------------
    const state = {
        tgUser: null,
        initData: "",
        companyWallets: {},
        selectedCrypto: "USDT",
        userWalletAddress: "",
        uploadedProofBase64: null,
        isSubmitting: false
    };

    // Initialize Lucide icons safely
    if (window.lucide) {
        try {
            lucide.createIcons();
        } catch (e) {
            console.error("Lucide icon generation failed:", e);
        }
    }

    // -------------------------------------------------------------
    // UI Elements Selection
    // -------------------------------------------------------------
    const elements = {
        loader: document.getElementById("loader"),
        toastContainer: document.getElementById("toast-container"),
        
        // User Profile
        userAvatar: document.getElementById("user-avatar"),
        avatarInitials: document.getElementById("avatar-initials"),
        userFullname: document.getElementById("user-fullname"),
        userUsername: document.getElementById("user-username"),
        userTgid: document.getElementById("user-tgid"),
        
        // Wallet State Columns
        walletDisconnected: document.getElementById("wallet-disconnected"),
        walletConnecting: document.getElementById("wallet-connecting"),
        walletConnected: document.getElementById("wallet-connected"),
        btnConnectWallet: document.getElementById("btn-connect-wallet"),
        btnDisconnectWallet: document.getElementById("btn-disconnect-wallet"),
        displayWalletAddress: document.getElementById("display-wallet-address"),
        btnCopyUserWallet: document.getElementById("btn-copy-user-wallet"),
        
        // Exchange Form
        exchangeSection: document.getElementById("exchange-section"),
        exchangeLockOverlay: document.getElementById("exchange-lock-overlay"),
        cryptoOptions: document.querySelectorAll(".crypto-option"),
        companyWalletAddress: document.getElementById("company-wallet-address"),
        btnCopyCompanyWallet: document.getElementById("btn-copy-company-wallet"),
        inputAmount: document.getElementById("input-amount"),
        amountCryptoSuffix: document.getElementById("amount-crypto-suffix"),
        inputHash: document.getElementById("input-hash"),
        fileUploadZone: document.getElementById("file-upload-zone"),
        inputProofImage: document.getElementById("input-proof-image"),
        uploadPrompt: document.getElementById("upload-prompt"),
        uploadPreviewContainer: document.getElementById("upload-preview-container"),
        uploadPreviewImg: document.getElementById("upload-preview-img"),
        btnRemoveProof: document.getElementById("btn-remove-proof"),
        btnSubmitTx: document.getElementById("btn-submit-tx"),
        p2pForm: document.getElementById("p2p-exchange-form"),
        
        // Transaction History
        historyLoading: document.getElementById("history-loading"),
        historyEmpty: document.getElementById("history-empty"),
        historyList: document.getElementById("history-list"),
        
        // Success Modal
        successModal: document.getElementById("success-modal"),
        successRefId: document.getElementById("success-ref-id"),
        successAmount: document.getElementById("success-amount"),
        btnCloseSuccess: document.getElementById("btn-close-success")
    };

    // -------------------------------------------------------------
    // Telegram Web App SDK Configuration
    // -------------------------------------------------------------
    const tg = window.Telegram.WebApp;
    
    // Notify Telegram that the app is ready and expand it
    tg.ready();
    tg.expand();
    
    // Apply Telegram theme colors to header if available
    if (tg.themeParams && tg.themeParams.bg_color) {
        document.documentElement.style.setProperty('--bg-primary', tg.themeParams.bg_color);
    }
    if (tg.themeParams && tg.themeParams.secondary_bg_color) {
        document.documentElement.style.setProperty('--bg-secondary', tg.themeParams.secondary_bg_color);
    }

    // Load Telegram User Info
    state.initData = tg.initData || "";
    
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        state.tgUser = tg.initDataUnsafe.user;
        renderUserProfile(state.tgUser);
    } else {
        // Falling back to mock user for browser preview
        console.warn("Telegram WebApp user context not found. Loading developer preview...");
        state.tgUser = {
            id: 123456789,
            first_name: "Demo",
            last_name: "Trader",
            username: "demo_p2p_trader"
        };
        renderUserProfile(state.tgUser);
    }


    // -------------------------------------------------------------
    // Init Setup Functions
    // -------------------------------------------------------------
    async function initializeApp() {
        try {
            // Fetch configuration details from backend API
            const response = await fetch("/api/config");
            if (!response.ok) throw new Error("Failed to load server configurations");
            
            const config = await response.json();
            state.companyWallets = config.company_wallets || {};
            
            // Set initial wallet address
            updateCompanyWalletDisplay();
            
            // Fetch and render initial transaction history
            await fetchTransactionHistory();
            
        } catch (error) {
            console.error("Initialization error:", error);
            showToast("Server communication error. Please try again later.", "error");
        } finally {
            // Hide full screen splash loader with transition delay
            setTimeout(() => {
                elements.loader.classList.add("fade-out");
            }, 600);
        }
    }

    function renderUserProfile(user) {
        const firstName = user.first_name || "";
        const lastName = user.last_name || "";
        const fullName = `${firstName} ${lastName}`.trim() || "Telegram User";
        
        elements.userFullname.textContent = fullName;
        
        if (user.username) {
            elements.userUsername.textContent = `@${user.username}`;
            elements.userUsername.classList.remove("hidden");
        } else {
            elements.userUsername.classList.add("hidden");
        }
        
        elements.userTgid.textContent = user.id;
        
        // Compute Avatar Initials
        const initials = ((firstName[0] || "") + (lastName[0] || "")).toUpperCase();
        elements.avatarInitials.textContent = initials || "U";
    }

    // -------------------------------------------------------------
    // Toast Notification System
    // -------------------------------------------------------------
    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        
        let iconName = "info";
        if (type === "success") iconName = "check-circle";
        if (type === "error") iconName = "alert-triangle";
        
        toast.innerHTML = `
            <i data-lucide="${iconName}" class="toast-icon"></i>
            <span>${message}</span>
        `;
        
        elements.toastContainer.appendChild(toast);
        if (window.lucide) {
            try {
                lucide.createIcons({ attrs: { class: 'toast-icon' } });
            } catch (e) {
                console.error("Lucide icon generation failed inside toast:", e);
            }
        }
        
        // Auto fade out
        setTimeout(() => {
            toast.classList.add("fade-out");
            toast.addEventListener("animationend", () => {
                toast.remove();
            });
        }, 3000);
    }

    // -------------------------------------------------------------
    // Crypto Asset Selection Handling
    // -------------------------------------------------------------
    elements.cryptoOptions.forEach(option => {
        option.addEventListener("click", () => {
            elements.cryptoOptions.forEach(opt => opt.classList.remove("active"));
            option.classList.add("active");
            
            state.selectedCrypto = option.getAttribute("data-crypto");
            
            // Update labels
            elements.amountCryptoSuffix.textContent = state.selectedCrypto;
            updateCompanyWalletDisplay();
        });
    });

    function updateCompanyWalletDisplay() {
        const wallet = state.companyWallets[state.selectedCrypto] || "No wallet configured";
        elements.companyWalletAddress.textContent = wallet;
    }

    // -------------------------------------------------------------
    // Clipboard Action Handles
    // -------------------------------------------------------------
    function copyToClipboard(text, successMsg) {
        if (!text || text.includes("Fetching") || text.includes("No wallet")) return;
        
        navigator.clipboard.writeText(text)
            .then(() => {
                showToast(successMsg, "success");
            })
            .catch(err => {
                console.error("Clipboard copy failed:", err);
                showToast("Failed to copy. Please manually select and copy.", "error");
            });
    }

    elements.btnCopyCompanyWallet.addEventListener("click", () => {
        copyToClipboard(elements.companyWalletAddress.textContent, "Admin wallet address copied!");
    });

    elements.btnCopyUserWallet.addEventListener("click", () => {
        copyToClipboard(state.userWalletAddress, "Your wallet address copied!");
    });

    // -------------------------------------------------------------
    // Mock Wallet Integration System
    // -------------------------------------------------------------
    elements.btnConnectWallet.addEventListener("click", () => {
        // Transition to connecting state
        elements.walletDisconnected.classList.remove("active");
        elements.walletDisconnected.classList.add("hidden");
        elements.walletConnecting.classList.remove("hidden");
        elements.walletConnecting.classList.add("active");
        
        // Simulate block signature authorization delay
        setTimeout(() => {
            // Generate realistic looking network addresses
            let mockAddress = "";
            if (state.selectedCrypto === "TON") {
                mockAddress = "EQD" + Array.from({length: 45}, () => "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_".charAt(Math.floor(Math.random() * 64))).join("");
            } else if (state.selectedCrypto === "BTC") {
                mockAddress = "bc1q" + Array.from({length: 38}, () => "abcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random() * 36))).join("");
            } else {
                // EVM-compatible wallets
                mockAddress = "0x" + Array.from({length: 40}, () => "0123456789abcdef".charAt(Math.floor(Math.random() * 16))).join("");
            }
            
            state.userWalletAddress = mockAddress;
            
            // Format address for display (e.g. 0xabcd...7890)
            const displayedAddr = mockAddress.length > 15 
                ? `${mockAddress.slice(0, 6)}...${mockAddress.slice(-4)}`
                : mockAddress;
                
            elements.displayWalletAddress.textContent = displayedAddr;
            
            // Swap state blocks
            elements.walletConnecting.classList.remove("active");
            elements.walletConnecting.classList.add("hidden");
            elements.walletConnected.classList.remove("hidden");
            elements.walletConnected.classList.add("active");
            
            // Enable exchange card details form
            elements.exchangeSection.classList.remove("disabled-card");
            elements.exchangeLockOverlay.classList.add("hidden");
            elements.btnSubmitTx.removeAttribute("disabled");
            
            showToast("Crypto Wallet connected successfully!", "success");
        }, 1500);
    });

    elements.btnDisconnectWallet.addEventListener("click", () => {
        state.userWalletAddress = "";
        
        // Swap state blocks
        elements.walletConnected.classList.remove("active");
        elements.walletConnected.classList.add("hidden");
        elements.walletDisconnected.classList.remove("hidden");
        elements.walletDisconnected.classList.add("active");
        
        // Lock and disable inputs
        elements.exchangeSection.classList.add("disabled-card");
        elements.exchangeLockOverlay.classList.remove("hidden");
        elements.btnSubmitTx.setAttribute("disabled", "true");
        
        showToast("Wallet disconnected.", "info");
    });

    // -------------------------------------------------------------
    // Image Upload & Validation Handlers
    // -------------------------------------------------------------
    
    // Drag & Drop triggers
    elements.fileUploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        elements.fileUploadZone.style.borderColor = "var(--primary-color)";
    });
    
    elements.fileUploadZone.addEventListener("dragleave", () => {
        elements.fileUploadZone.style.borderColor = "var(--border-color)";
    });
    
    elements.fileUploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        elements.fileUploadZone.style.borderColor = "var(--border-color)";
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    elements.inputProofImage.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    function handleFileUpload(file) {
        // Size validation: limit to 5MB
        if (file.size > 5 * 1024 * 1024) {
            showToast("Proof image size exceeds 5MB limit", "error");
            return;
        }
        
        // Mime Type validation
        if (!file.type.startsWith("image/")) {
            showToast("Only standard image receipts are supported", "error");
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (event) => {
            state.uploadedProofBase64 = event.target.result;
            
            // Show preview
            elements.uploadPreviewImg.src = event.target.result;
            elements.uploadPrompt.classList.add("hidden");
            elements.uploadPreviewContainer.classList.remove("hidden");
            showToast("Proof screenshot parsed successfully", "success");
        };
        reader.readAsDataURL(file);
    }

    elements.btnRemoveProof.addEventListener("click", (e) => {
        e.stopPropagation(); // prevent file input click trigger
        clearUploadedProof();
    });

    function clearUploadedProof() {
        state.uploadedProofBase64 = null;
        elements.inputProofImage.value = "";
        elements.uploadPreviewContainer.classList.add("hidden");
        elements.uploadPrompt.classList.remove("hidden");
    }

    // -------------------------------------------------------------
    // Transaction History API Loading & Rendering
    // -------------------------------------------------------------
    async function fetchTransactionHistory() {
        elements.historyLoading.classList.remove("hidden");
        elements.historyLoading.classList.add("active");
        elements.historyEmpty.classList.add("hidden");
        elements.historyList.classList.add("hidden");
        
        try {
            const queryParams = new URLSearchParams({
                initData: state.initData
            });
            const response = await fetch(`/api/transactions?${queryParams.toString()}`);
            if (!response.ok) throw new Error("Could not retrieve logs");
            
            const data = await response.json();
            const txs = data.transactions || [];
            
            renderTransactionsList(txs);
        } catch (error) {
            console.error("Error fetching transactions:", error);
            // Non-blocking UI error display
            elements.historyLoading.classList.add("hidden");
            elements.historyEmpty.classList.remove("hidden");
        }
    }

    function renderTransactionsList(transactions) {
        elements.historyLoading.classList.add("hidden");
        
        if (!transactions || transactions.length === 0) {
            elements.historyEmpty.classList.remove("hidden");
            elements.historyList.classList.add("hidden");
            return;
        }
        
        elements.historyEmpty.classList.add("hidden");
        elements.historyList.innerHTML = "";
        
        transactions.forEach(tx => {
            // Formate Date
            let dateStr = "N/A";
            if (tx.timestamp) {
                try {
                    const date = new Date(tx.timestamp);
                    dateStr = date.toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                } catch(e) {
                    dateStr = tx.timestamp.slice(0, 16);
                }
            }
            
            // Format status badge
            const statusLabel = tx.status || "Pending Verification";
            const statusClass = statusLabel.toLowerCase().includes("verified") 
                ? "status-verified" 
                : "status-pending";
            
            // Truncate hash
            const shortHash = tx.transaction_hash && tx.transaction_hash.length > 12
                ? `${tx.transaction_hash.slice(0, 8)}...${tx.transaction_hash.slice(-4)}`
                : tx.transaction_hash || "N/A";
            
            // Crypto icon character
            let iconChar = "₮";
            if (tx.crypto_type === "BTC") iconChar = "₿";
            if (tx.crypto_type === "ETH") iconChar = "♦";
            if (tx.crypto_type === "TON") iconChar = "💎";
            
            const item = document.createElement("div");
            item.className = "history-item";
            item.innerHTML = `
                <div class="history-item-left">
                    <div class="history-item-icon">${iconChar}</div>
                    <div class="history-item-info">
                        <span class="history-item-title">Sell ${tx.crypto_type}</span>
                        <span class="history-item-date">${dateStr}</span>
                        <span class="history-item-hash">TXID: <span class="code-font">${shortHash}</span></span>
                    </div>
                </div>
                <div class="history-item-right">
                    <span class="history-item-amount">${tx.amount} ${tx.crypto_type}</span>
                    <span class="status-badge ${statusClass}">${statusLabel}</span>
                </div>
            `;
            elements.historyList.appendChild(item);
        });
        
        elements.historyList.classList.remove("hidden");
    }

    // -------------------------------------------------------------
    // Exchange Form Submit API Process
    // -------------------------------------------------------------
    elements.p2pForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        if (state.isSubmitting) return;
        
        const amountStr = elements.inputAmount.value.trim();
        const hashStr = elements.inputHash.value.trim();
        
        // Input validation
        if (!amountStr || isNaN(amountStr) || parseFloat(amountStr) <= 0) {
            showToast("Please enter a valid amount to exchange", "error");
            return;
        }
        
        if (!hashStr || hashStr.length < 8) {
            showToast("Please enter a valid transaction hash ID", "error");
            return;
        }
        
        try {
            setSubmitState(true);
            
            const payload = {
                initData: state.initData,
                crypto_type: state.selectedCrypto,
                amount: parseFloat(amountStr),
                transaction_hash: hashStr,
                wallet_address: state.userWalletAddress,
                proof_image: state.uploadedProofBase64
            };
            
            const response = await fetch("/api/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || "Submit failed on database write");
            }
            
            // Handle success
            showToast("Transaction submitted successfully!", "success");
            
            // Format Modal values
            elements.successRefId.textContent = `#${result.transaction.id || "000"}`;
            elements.successAmount.textContent = `${result.transaction.amount} ${result.transaction.crypto_type}`;
            
            // Reset forms
            elements.p2pForm.reset();
            clearUploadedProof();
            
            // Display modal
            elements.successModal.classList.remove("hidden");
            
            // Fetch updated logs
            await fetchTransactionHistory();
            
        } catch (error) {
            console.error("Submission error:", error);
            showToast(error.message || "Failed to submit transaction details. Try again.", "error");
        } finally {
            setSubmitState(false);
        }
    });

    function setSubmitState(submitting) {
        state.isSubmitting = submitting;
        if (submitting) {
            elements.btnSubmitTx.setAttribute("disabled", "true");
            elements.btnSubmitTx.innerHTML = `<div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div> Processing submission...`;
        } else {
            elements.btnSubmitTx.removeAttribute("disabled");
            elements.btnSubmitTx.textContent = "Submit Transaction for Verification";
        }
    }

    elements.btnCloseSuccess.addEventListener("click", () => {
        elements.successModal.classList.add("hidden");
    });

    // Handle background modal closing clicks
    elements.successModal.addEventListener("click", (e) => {
        if (e.target === elements.successModal) {
            elements.successModal.classList.add("hidden");
        }
    });

    // -------------------------------------------------------------
    // Initializer Boot
    // -------------------------------------------------------------
    initializeApp();
});
