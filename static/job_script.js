document.getElementById("jobForm").addEventListener("submit", function (event) {
  event.preventDefault();

  // Check user role before submitting (optional but can save an API call)
  const userRole = sessionStorage.getItem("userRole"); // You'll need to set this when user logs in
  if (userRole && userRole.toLowerCase() !== "recruiter") {
      showErrorPopup("Access denied: You must be a recruiter to post jobs.");
      return;
  }

  const formData = new FormData(event.target);
  const jobData = {
      title: formData.get("title"),
      company: formData.get("company"),
      description: formData.get("description"),
      location: formData.get("location"),
      experience: formData.get("experience"),
      skills: formData.get("skills"),
      job_type: formData.get("job_type"),
      status: "Open"
  };

  fetch("/job_post", {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify(jobData)
  })
  .then(response => {
      if (!response.ok) {
          // If response status is 403 (Forbidden) or other error status
          return response.json().then(errData => {
              throw new Error(errData.message || "Access denied");
          });
      }
      return response.json();
  })
  .then(data => {
      if (data.success) {
          alert("✅ Job posted successfully!");
          // Store and display jobs
          const jobs = JSON.parse(sessionStorage.getItem("jobs")) || [];
          jobs.push(jobData);
          sessionStorage.setItem("jobs", JSON.stringify(jobs));

          if (typeof displayJobs === "function") {
              displayJobs();
          }
      } else {
          showErrorPopup(data.message);
      }
  })
  .catch(error => {
      console.error("🚨 Fetch error:", error);
      showErrorPopup(error.message || "⚠️ Could not connect to server");
  });
});

// Function to show error popup
function showErrorPopup(message) {
  // Create popup element if it doesn't exist
  let popup = document.getElementById("errorPopup");
  if (!popup) {
      popup = document.createElement("div");
      popup.id = "errorPopup";
      popup.style.position = "fixed";
      popup.style.top = "20px";
      popup.style.right = "20px";
      popup.style.padding = "15px";
      popup.style.backgroundColor = "#ffebee";
      popup.style.color = "#c62828";
      popup.style.border = "1px solid #ef9a9a";
      popup.style.borderRadius = "4px";
      popup.style.zIndex = "1000";
      popup.style.boxShadow = "0 2px 10px rgba(0,0,0,0.1)";
      popup.style.maxWidth = "300px";
      
      const closeBtn = document.createElement("button");
      closeBtn.textContent = "×";
      closeBtn.style.float = "right";
      closeBtn.style.border = "none";
      closeBtn.style.background = "none";
      closeBtn.style.cursor = "pointer";
      closeBtn.style.fontSize = "16px";
      closeBtn.addEventListener("click", () => {
          popup.remove();
      });
      
      popup.appendChild(closeBtn);
      document.body.appendChild(popup);
  }
  
  // Add message content
  const messageEl = document.createElement("div");
  messageEl.textContent = message;
  messageEl.style.marginRight = "20px"; // Space for close button
  
  // Clear previous messages
  while (popup.childNodes.length > 1) {
      popup.removeChild(popup.lastChild);
  }
  popup.insertBefore(messageEl, popup.firstChild.nextSibling);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
      if (popup.parentNode) {
          popup.remove();
      }
  }, 5000);
}

  const carousel = document.getElementById('carousel');
  const nextBtn = document.querySelector('.next');
  const prevBtn = document.querySelector('.prev');

  const scrollAmount = 200; // Adjust based on card width

  nextBtn.addEventListener('click', () => {
    carousel.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  });

  prevBtn.addEventListener('click', () => {
    carousel.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
  });

  // Swipe Support (Mobile touch)
  let isDown = false;
  let startX;
  let scrollLeft;

  carousel.addEventListener('touchstart', (e) => {
    isDown = true;
    startX = e.touches[0].pageX - carousel.offsetLeft;
    scrollLeft = carousel.scrollLeft;
  });

  carousel.addEventListener('touchmove', (e) => {
    if (!isDown) return;
    const x = e.touches[0].pageX - carousel.offsetLeft;
    const walk = (startX - x); // how far to scroll
    carousel.scrollLeft = scrollLeft + walk;
  });

  carousel.addEventListener('touchend', () => {
    isDown = false;
  });
