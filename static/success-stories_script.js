const alumniData = [
    { 
        name: "Mr.Ravikumar",
      
        gradYear: 2008,
        achievements: "Built a billion-dollar AI healthcare startup.",
        industryImpact: "Revolutionized AI-driven medical diagnostics.",
        milestones: ["Founded HealthTech AI", "Awarded Top Innovator 2018", "Expanded to 20 countries"],
        testimonial: "The best decision of my life was joining this university. It shaped my vision."
    },
    { 
        name: "Dr.Prabakaran",
       
        gradYear: 2012,
        achievements: "Pioneered AI ethics research, influencing global policies.",
        industryImpact: "Helped create ethical AI frameworks adopted by major tech firms.",
        milestones: ["Published 10 AI research papers", "Advised UN on AI Ethics", "Won AI Innovator Award"],
        testimonial: "The faculty and research facilities here ignited my passion for AI ethics."
    },
    { 
        name: "Mr.Vijaykumar",
     
        gradYear: 2015,
        achievements: "Led human rights cases worldwide.",
        industryImpact: "Shaped global policies on social justice and equity.",
        milestones: ["Fought landmark case for refugee rights", "Published book on human rights", "Worked with UN Human Rights Council"],
        testimonial: "My time here equipped me with the skills to bring justice to those in need."
    },
    { 
        name: "Dr.Parthiban",
        
        gradYear: 2010,
        achievements: "Transformed finance sector with blockchain innovations.",
        industryImpact: "Created secure digital banking solutions for developing nations.",
        milestones: ["Founded FinTech startup", "Partnered with global banks", "Featured in Forbes 30 Under 30"],
        testimonial: "I owe my success to the education and mentorship I received here."
    },
    { 
        name: "Mr.Vinayagam",
        
        gradYear: 2011,
        achievements: "Made breakthroughs in cancer treatment with biotechnology.",
        industryImpact: "Developed revolutionary cancer detection methods.",
        milestones: ["Discovered novel cancer biomarker", "Published 50+ research papers", "Received Nobel Prize in Medicine"],
        testimonial: "The research culture here nurtured my curiosity and drive for medical innovation."
    }
];

let currentIndex = 0;
const totalCards = alumniData.length;
const visibleCards = 3;

function updateVisibility() {
    const container = document.querySelector(".carousel-container");
    container.innerHTML = ""; // Clear previous elements

    for (let i = currentIndex; i < currentIndex + visibleCards; i++) {
        if (i >= totalCards) break;

        const alumni = alumniData[i];
        const card = document.createElement("div");
        card.classList.add("card");

        if (i % 2 === 0) {
            card.classList.add("left-swing");
        } else {
            card.classList.add("right-swing");
        }

        card.innerHTML = `
            
            <h3>${alumni.name}</h3>
            <p>Class of ${alumni.gradYear}</p>
        `;

        // Ensure click event is correctly bound
        card.addEventListener("click", function () {
            console.log("Card clicked:", alumni.name);
            openProfile(i);
        });

        container.appendChild(card);
    }
}



function moveSlide(direction) {
    const maxIndex = totalCards - visibleCards;
    currentIndex += direction;

    if (currentIndex < 0) currentIndex = 0;
    if (currentIndex > maxIndex) currentIndex = maxIndex;

    updateVisibility();
}
function openProfile(index) {
    const alumni = alumniData[index];
    console.log("Opening profile for:", alumni.name);
    
    // Force redirect
    window.location.replace(`/alumni-profile?name=${encodeURIComponent(alumni.name)}`);
}



// Ensure cards are displayed correctly on page load
document.addEventListener("DOMContentLoaded", updateVisibility);