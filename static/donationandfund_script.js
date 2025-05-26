// Store campaigns dynamically
let campaigns = [];
let currentCampaignIndex = -1;

// Initialize modals
const modals = {
    donation: document.getElementById("donationModal"),
    payment: document.getElementById("paymentModal"),
    success: document.getElementById("successModal")
};

// Open modals
document.getElementById("openModal").addEventListener("click", () => {
    modals.donation.style.display = "block";
});

// Close modals
document.querySelector(".close").addEventListener("click", () => {
    modals.donation.style.display = "none";
});

document.querySelector(".close-payment").addEventListener("click", () => {
    modals.payment.style.display = "none";
});

document.getElementById("closeSuccess").addEventListener("click", () => {
    modals.success.style.display = "none";
    modals.payment.style.display = "none";
});

// Close modal if user clicks outside it
window.addEventListener("click", (event) => {
    if (event.target === modals.donation) {
        modals.donation.style.display = "none";
    }
    if (event.target === modals.payment) {
        modals.payment.style.display = "none";
    }
    if (event.target === modals.success) {
        modals.success.style.display = "none";
    }
});

// Create new campaign
document.getElementById("createCampaign").addEventListener("click", function () {
    let name = document.getElementById("campaignName").value;
    let target = document.getElementById("targetAmount").value;
    let description = document.getElementById("campaignDescription").value;

    if (name && target && description) {
        let campaign = {
            name: name,
            target: target,
            description: description,
            raised: 0
        };

        campaigns.push(campaign);
        updateCampaigns();
        modals.donation.style.display = "none";
        
        // Clear form
        document.getElementById("campaignName").value = "";
        document.getElementById("targetAmount").value = "";
        document.getElementById("campaignDescription").value = "";
    }
});

// Update campaigns display
async function updateCampaigns() {
    try {
        // Fetch latest campaign totals from server
        const response = await fetch('/get-campaign-totals');
        const campaignTotals = await response.json();
        
        // Update our local campaigns array with live data
        campaigns.forEach(campaign => {
            if (campaignTotals[campaign.name]) {
                campaign.raised = campaignTotals[campaign.name];
            }
        });
        
        // Render the updated campaigns
        let campaignContainer = document.getElementById("campaigns");
        campaignContainer.innerHTML = '';
        
        campaigns.forEach((campaign, index) => {
            let campaignCard = document.createElement("div");
            campaignCard.classList.add("campaign");
            
            campaignCard.innerHTML = `
                <h3>${campaign.name}</h3>
                <p>${campaign.description}</p>
                <p><strong>Goal:</strong> ₹${campaign.target}</p>
                <progress value="${campaign.raised}" max="${campaign.target}"></progress>
                <p><strong>Raised:</strong> ₹${campaign.raised}</p>
                <button onclick="openDonationModal(${index})">Donate</button>
            `;
            
            campaignContainer.appendChild(campaignCard);
        });
        
    } catch (error) {
        console.error("Error updating campaigns:", error);
        // Fallback to local data if API fails
        renderLocalCampaigns();
    }
}

// Fallback function using local data only
function renderLocalCampaigns() {
    let campaignContainer = document.getElementById("campaigns");
    campaignContainer.innerHTML = '';
    
    campaigns.forEach((campaign, index) => {
        let campaignCard = document.createElement("div");
        campaignCard.classList.add("campaign");
        
        campaignCard.innerHTML = `
            <h3>${campaign.name}</h3>
            <p>${campaign.description}</p>
            <p><strong>Goal:</strong> ₹${campaign.target}</p>
            <progress value="${campaign.raised}" max="${campaign.target}"></progress>
            <p><strong>Raised:</strong> ₹${campaign.raised}</p>
            <button onclick="openDonationModal(${index})">Donate</button>
        `;
        
        campaignContainer.appendChild(campaignCard);
    });
}

// Open donation modal
function openDonationModal(index) {
    currentCampaignIndex = index;
    const campaign = campaigns[index];
    
    document.getElementById("paymentCampaignInfo").innerHTML = `
        <h3>${campaign.name}</h3>
        <p>${campaign.description}</p>
        <p>Goal: ₹${campaign.target} | Raised: ₹${campaign.raised}</p>
    `;
    
    document.getElementById("donationAmount").value = "";
    document.getElementById("paymentStatus").innerHTML = "";
    modals.payment.style.display = "block";
}

// Handle payment
document.getElementById("proceedToPay").addEventListener("click", async function() {
    const amount = document.getElementById("donationAmount").value;
    const campaign = campaigns[currentCampaignIndex];
    
    if (!amount || isNaN(amount)) {
        document.getElementById("paymentStatus").innerHTML = "Please enter a valid amount";
        return;
    }
    
    if (amount < 1) {
        document.getElementById("paymentStatus").innerHTML = "Minimum donation is ₹1";
        return;
    }
    
    try {
        // Create order on the server
        const response = await fetch('/create-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: amount * 100, // Convert to paise
                currency: "INR",
                receipt: "donation_" + Date.now(),
                notes: {
                    campaign: campaign.name,
                    donor: "User"
                }
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create order');
        }
        
        const order = await response.json();
        
        const options = {
            key: "rzp_test_ekuUcHA0UOfU6z",
            amount: order.amount,
            currency: order.currency,
            name: "Alumnexus",
            description: `Donation to ${campaign.name}`,
            image: "https://example.com/your_logo.jpg",
            order_id: order.id,
            modal: {
                ondismiss: function() {
                    // This will be called when payment is cancelled
                    document.getElementById("paymentStatus").innerHTML = `
                        <div class="payment-cancelled">
                            <p>Payment was cancelled</p>
                            <button onclick="retryPayment()" class="retry-btn">Retry Payment</button>
                        </div>
                    `;
                }
            },
            handler: async function(response) {
                try {
                    // Verify payment on server
                    const verificationResponse = await fetch('/verify-payment', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(response)
                    });
            
                    const result = await verificationResponse.json();
            
                    // Only if server confirms success
                    if (result.status === 'success') {
                        // Update local campaigns array immediately
                        campaigns[currentCampaignIndex].raised += parseInt(amount);
                        
                        // Refresh campaigns from server to get accurate totals
                        await updateCampaigns();
                        
                        document.getElementById("successMessage").innerHTML = `
                            Payment Successful!<br><br>
                            Thank you for your donation of ₹${amount} to ${campaigns[currentCampaignIndex].name}!<br>
                            Transaction ID: ${response.razorpay_payment_id}
                        `;
                        modals.success.style.display = "block";
                    } else {
                        throw new Error("Verification failed at server");
                    }
                } catch (error) {
                    console.error("Verification error:", error);
                    document.getElementById("paymentStatus").innerHTML = `
                        <div class="payment-error">
                            <p>❌ Payment verification failed. Please try again.</p>
                            <button onclick="retryPayment()" class="retry-btn">Retry Payment</button>
                            <button onclick="showAlternativeMethods()" class="alt-method-btn">Other Payment Methods</button>
                        </div>
                    `;
                }
            },
            prefill: {
                name: "Ram Kumar",
                email: "john.doe@example.com",
                contact: "9876543210"
            },
            notes: {
                campaign: campaign.name
            },
            theme: {
                color: "#3399cc"
            }
        };
        
        const rzp = new Razorpay(options);

        rzp.on('payment.failed', function (response) {
            console.error("❌ Payment Failed", response);
            let errorMsg = response.error.description || "Unknown error";
            
            // Check if this was a user cancellation
            if (response.error.code === 'payment_cancelled') {
                errorMsg = "Payment was cancelled by user";
            }
            
            document.getElementById("paymentStatus").innerHTML = `
                <div class="payment-error">
                    <p>Payment failed ❌</p>
                    <p>Reason: ${errorMsg}</p>
                    <button onclick="retryPayment()" class="retry-btn">Retry Payment</button>
                    <button onclick="showAlternativeMethods()" class="alt-method-btn">Other Payment Methods</button>
                </div>
            `;
            modals.success.style.display = "none";
        });
        
        rzp.open();
        
    } catch (error) {
        console.error("Payment error:", error);
        document.getElementById("paymentStatus").innerHTML = `
            <div class="payment-error">
                <p>Payment processing failed. Please try again.</p>
                <button onclick="retryPayment()" class="retry-btn">Retry Payment</button>
                <button onclick="showAlternativeMethods()" class="alt-method-btn">Other Payment Methods</button>
            </div>
        `;
    }
});

// Retry payment function
function retryPayment() {
    document.getElementById("paymentStatus").innerHTML = "";
    document.getElementById("donationAmount").value = "";
    document.getElementById("proceedToPay").click();
}

// Show alternative payment methods
function showAlternativeMethods() {
    document.getElementById("paymentStatus").innerHTML = `
        <div class="alternative-methods">
            <h4>Alternative Payment Methods</h4>
            <p>You can also donate via:</p>
            <ul>
                <li>Bank Transfer: Account No. 1234567890, IFSC: ALUM0001</li>
                <li>UPI: alumnexus@upi</li>
                <li>Check/Cash (Contact alumni office at alumni@alumnexus.edu)</li>
            </ul>
            <button onclick="closeAlternativeMethods()" class="close-alt-btn">Back to Card Payment</button>
        </div>
    `;
}

// Close alternative methods view
function closeAlternativeMethods() {
    document.getElementById("paymentStatus").innerHTML = "";
}

// Search bar functionality
document.getElementById("searchBar").addEventListener("input", function (e) {
    let value = e.target.value.toLowerCase();
    document.querySelectorAll('.campaign').forEach(campaign => {
        let title = campaign.querySelector('h3').textContent.toLowerCase();
        campaign.style.display = title.includes(value) ? 'block' : 'none';
    });
});

// Initialize with some sample campaigns
// Initialize campaigns when page loads
document.addEventListener('DOMContentLoaded', async function() {
    // Default campaigns (fallback if API fails)
    campaigns = [
        {
            name: "Scholarship Fund",
            description: "Support deserving students with financial aid",
            target: 10000,
            raised: 3500
        },
        {
            name: "Campus Renovation",
            description: "Help renovate the old library building",
            target: 5000,
            raised: 1200
        }
    ];
    
    // Fetch live data from the server
    await updateCampaigns();
    
    // Load donation history
    loadDonationHistory();
});

async function loadDonationHistory() {
    try {
        const response = await fetch('/get-donation-history');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to load donation history');
        }
        
        const donations = await response.json();
        const historyContainer = document.getElementById('donationHistory');
        
        if (donations.length === 0) {
            historyContainer.innerHTML = '<p>You have not made any donations yet.</p>';
            return;
        }
        
        historyContainer.innerHTML = donations.map(donation => `
            <div class="donation-record">
                <div>
                    <h4>${donation.campaign_name}</h4>
                    <p>Amount: ₹${donation.amount}</p>
                    <p>Date: ${new Date(donation.donation_date).toLocaleDateString()}</p>
                </div>
                <button class="receipt-btn" onclick="generateReceipt('${donation.transaction_id}')">
                    View Receipt
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading donation history:', error);
        document.getElementById('donationHistory').innerHTML = `
            <div class="error-message">
                <p>Error loading donation history: ${error.message}</p>
                <button onclick="loadDonationHistory()">Retry</button>
            </div>
        `;
    }
}

function generateReceipt(transactionId) {
    window.open(`/generate-receipt/${transactionId}`, '_blank');
}

