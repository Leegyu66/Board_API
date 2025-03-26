const API_URL = "http://localhost:8080";  // 백엔드 API URL
const loginForm = document.getElementById("loginForm");
const logoutButton = document.getElementById("logoutButton");
const boardSection = document.getElementById("boardSection");
const boardList = document.getElementById("boardList");
const createPostButton = document.getElementById("createPostButton");
const createPostForm = document.getElementById("createPostForm");
const submitPostButton = document.getElementById("submitPostButton");
const cancelPostButton = document.getElementById("cancelPostButton");
const postTitleInput = document.getElementById("postTitle");
const postContentInput = document.getElementById("postContent");
const editPostButton = document.getElementById("editPostButton");
const detailTitle = document.getElementById("detailTitle");
const detailContent = document.getElementById("detailContent");
const postDetails = document.getElementById("postDetails");
const detailViewcnt = document.getElementById("detailViewcnt")
const closePostDetailsButton = document.getElementById("closePostDetails");


let currentPostId = null;

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    
    try {
        const response = await axios.post(`${API_URL}/user/login`, new URLSearchParams({
            username,
            password
        }), {
            headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
        
        document.cookie = `access_token=${response.data.access_token}; path=/`;
        
        loginForm.style.display = "none";
        boardSection.style.display = "block";
        logoutButton.style.display = "inline-block";
        
        loadBoardPosts();
    } catch (error) {
        alert("Login failed!");
        console.error(error);
    }
});

closePostDetailsButton.addEventListener("click", () => {
    postDetails.style.display = "none";
});

logoutButton.addEventListener("click", async () => {
    try {
        await axios.post(`${API_URL}/user/logout`, {}, {
            headers: {
                "Authorization": `Bearer ${getCookie("access_token")}`
            }
        });
        document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        boardSection.style.display = "none";
        loginForm.style.display = "block";
        logoutButton.style.display = "none";
    } catch (error) {
        alert("Logout failed!");
        console.error(error);
    }
});

async function loadBoardPosts() {
    try {
        const response = await axios.get(`${API_URL}/board`, {
            headers: {
                "Authorization": `Bearer ${getCookie("access_token")}`
            }
        });

        boardList.innerHTML = "";
        response.data.forEach(post => {
            const listItem = document.createElement("li");
            listItem.textContent = post.title;

            listItem.addEventListener("click", async () => {
                try {
                    const res = await axios.get(`${API_URL}/board/${post.id}`, {
                        headers: {
                            "Authorization": `Bearer ${getCookie("access_token")}`
                        }
                    });

                    const board = res.data;
                    currentPostId = post.id;
                    detailTitle.textContent = board.title;
                    detailContent.textContent = board.content;
                    detailViewcnt.textContent = `View Count: ${board.view_cnt}`;
                    postDetails.style.display = "block";
                } catch (error) {
                    alert("글을 불러오는 데 실패했어요!");
                    console.error(error);
                }
            });

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "삭제";
            deleteButton.style.marginLeft = "10px";

            deleteButton.addEventListener("click", async (e) => {
                e.stopPropagation();
                if (confirm("정말 삭제하시겠습니까?")) {
                    try {
                        await axios.delete(`${API_URL}/board/${post.id}`, {
                            headers: {
                                "Authorization": `Bearer ${getCookie("access_token")}`
                            }
                        });
                        alert("삭제 완료!");
                        postDetails.style.display = "none";
                        loadBoardPosts();
                    } catch (error) {
                        alert("삭제 실패!");
                        console.error(error);
                    }
                }
            });

            listItem.appendChild(deleteButton);
            boardList.appendChild(listItem);
        });
    } catch (error) {
        alert("Failed to load board posts");
        console.error(error);
    }
}

createPostButton.addEventListener("click", () => {
    createPostForm.style.display = "block";
    submitPostButton.textContent = "Submit";
    currentPostId = null;
});

submitPostButton.addEventListener("click", async () => {
    const title = postTitleInput.value;
    const content = postContentInput.value;

    if (!title || !content) {
        alert("Both title and content are required.");
        return;
    }

    try {
        if (currentPostId) {
            // ✅ 수정
            await axios.patch(`${API_URL}/board/${currentPostId}`, {
                title,
                content
            }, {
                headers: {
                    "Authorization": `Bearer ${getCookie("access_token")}`
                }
            });
            alert("수정 완료!");
        } else {
            // ✅ 새 글 작성
            await axios.post(`${API_URL}/board`, {
                title,
                content
            }, {
                headers: {
                    "Authorization": `Bearer ${getCookie("access_token")}`
                }
            });
            alert("작성 완료!");
        }

        createPostForm.style.display = "none";
        submitPostButton.textContent = "Submit";
        currentPostId = null;
        loadBoardPosts();
    } catch (error) {
        alert("등록 실패!");
        console.error(error);
    }
});

cancelPostButton.addEventListener("click", () => {
    createPostForm.style.display = "none";
    submitPostButton.textContent = "Submit";
    currentPostId = null;
});

// ✅ 수정 버튼 클릭 시 폼에 기존 값 채우기
editPostButton.addEventListener("click", () => {
    if (!currentPostId) return;
    postTitleInput.value = detailTitle.textContent;
    postContentInput.value = detailContent.textContent;
    createPostForm.style.display = "block";
    submitPostButton.textContent = "Update";
    postDetails.style.display = "none";
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
}