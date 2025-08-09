document.addEventListener("DOMContentLoaded", function () {
  // follow/unfollow
  const followBtn = document.getElementById("follow-btn");
  if (followBtn) {
    followBtn.addEventListener("click", function () {
      const username = this.dataset.username;
      const csrftoken = getCookie("csrftoken");
      fetch("/ajax/toggle-follow/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "username=" + encodeURIComponent(username),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.status === "followed") {
            followBtn.textContent = "Unfollow";
          } else if (data.status === "unfollowed") {
            followBtn.textContent = "Follow";
          }
          // update follower count on page if present
          const followerCountEl = document.getElementById("follower-count");
          if (followerCountEl && data.followers_count !== undefined) {
            followerCountEl.textContent = data.followers_count;
          }
         
        });
    });
  }

  // post view increment
  if (window.BLOG && window.BLOG.postSlug) {
    const csrftoken = getCookie("csrftoken");
    fetch("/ajax/post-view/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: "slug=" + encodeURIComponent(window.BLOG.postSlug),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.views !== undefined) {
          const vc = document.getElementById("view-count");
          if (vc) vc.textContent = "Views: " + data.views;
        }
      });
  }

  // comment AJAX
  const commentForm = document.getElementById("comment-form");
  if (commentForm) {
    commentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const body = document.getElementById("comment-body").value;

      const csrftoken = getCookie("csrftoken");
      fetch("/ajax/add-comment/" + window.BLOG.postSlug + "/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "body=" + encodeURIComponent(body),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.status === "ok") {
            // Add new comment to list
            const list = document.getElementById("comment-list");
            const item = document.createElement("li");
            item.className = "bg-gray-50 p-3 rounded";
            item.innerHTML =
              '<p class="text-sm"><strong>' +
              data.comment.author +
              '</strong> · <span class="text-xs text-gray-500">' +
              data.comment.created_at +
              '</span></p><p class="mt-1">' +
              data.comment.body +
              "</p>";
            list.appendChild(item);
            const commentCountSpan = document.querySelector(".comment-count");
            console.log("Before update:", commentCountSpan.textContent);
            commentCountSpan.textContent = data.comments_count;
            document.getElementById("comment-body").value = "";
          } else {
            alert(data.error || "Error posting comment");
          }
        });
    });
  }

  // helper to get cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
