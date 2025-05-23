// 海龟汤游戏主逻辑 - 对话模式
document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('puzzle-display');
    const userInput = document.getElementById('user-guess');
    const submitBtn = document.getElementById('submit-guess');
    const getHintBtn = document.getElementById('get-hint');
    const solveBtn = document.getElementById('solve');
    let currentPuzzle = null;
    let currentPuzzleFile = null;
    let cluesGiven = [];

    // 保存状态到localStorage
    function saveState() {
        localStorage.setItem('hgtState', JSON.stringify({
            puzzle: currentPuzzle,
            file: currentPuzzleFile,
            clues: cluesGiven,
            chatHistory: document.getElementById('puzzle-display').innerHTML
        }));
    }

    // 从localStorage恢复状态
    function restoreState() {
        const saved = localStorage.getItem('hgtState');
        if (saved) {
            try {
                const state = JSON.parse(saved);
                currentPuzzle = state.puzzle;
                currentPuzzleFile = state.file;
                cluesGiven = state.clues || [];
                document.getElementById('puzzle-display').innerHTML = state.chatHistory || '';
                return true;
            } catch (e) {
                console.error('恢复状态失败:', e);
                localStorage.removeItem('hgtState');
            }
        }
        return false;
    }

    // 获取提示按钮
    getHintBtn.addEventListener('click', async () => {
        if (!currentPuzzle) return;
        
        const waitingSpan = addMessage('获取提示中...', 'bot');
        lockUI();
        
        try {
            const response = await callOpenRouterAPI([
                { role: "system", content: `你是一个海龟汤游戏主持人，根据以下谜题提供一个不泄露谜底的提示：
谜题: ${currentPuzzle}
规则:
1. 提示应该引导思考但不要直接给出答案
2. 提示应该简短明了` },
                { role: "user", content: "请给我一个提示" }
            ]);
            
            const container = document.createElement('div');
            container.className = 'message-container';
            
            const responseSpan = document.createElement('span');
            responseSpan.className = 'bot-message';
            responseSpan.textContent = response;
            container.appendChild(responseSpan);
            
            waitingSpan.parentNode.replaceChild(container, waitingSpan);
            saveState();
        } catch (error) {
            addMessage(`获取提示失败: ${error.message}`, 'error', waitingSpan.id);
        } finally {
            unlockUI();
        }
    });
    
    // 解答按钮
    solveBtn.addEventListener('click', () => {
        if (!currentPuzzle) return;
        
        const solutionMatch = currentPuzzle.match(/### 汤底([\s\S]*?)(###|$)/);
        if (solutionMatch) {
            addMessage('谜底：' + solutionMatch[1].trim(), 'bot');
            saveState();
        }
    });

    // 锁定UI
    function lockUI() {
        userInput.disabled = true;
        submitBtn.disabled = true;
        userInput.placeholder = "处理中...";
    }

    // 解锁UI
    function unlockUI() {
        userInput.disabled = false;
        submitBtn.disabled = false;
        userInput.placeholder = "输入你的猜测...";
        userInput.focus();
    }
    
    // 从URL参数获取puzzle文件名
    const urlParams = new URLSearchParams(window.location.search);
    const puzzleFile = urlParams.get('puzzle');
    
    // 处理URL参数中的谜题（不恢复状态）
    if (puzzleFile) {
        localStorage.removeItem('hgtState');
        loadPuzzle(puzzleFile);
    } 
    // 没有URL参数则尝试恢复状态或加载随机谜题
    else if (!restoreState()) {
        loadRandomPuzzle();
    }
    
    async function loadPuzzle(fileName) {
        try {
            // 完全重置状态
            localStorage.removeItem('hgtState');
            currentPuzzle = null;
            currentPuzzleFile = null;
            cluesGiven = [];
            chatContainer.innerHTML = '';
            
            const response = await fetch(`/puzzles/${fileName}`);
            currentPuzzle = await response.text();
            currentPuzzleFile = fileName;
            
            // 更健壮的谜题内容解析
            const puzzleParts = currentPuzzle.split('### 汤面');
            if (puzzleParts.length < 2) {
                throw new Error('无效的谜题格式: 缺少汤面部分');
            }
            
            const solutionParts = puzzleParts[1].split('### 汤底');
            if (solutionParts.length < 2) {
                throw new Error('无效的谜题格式: 缺少汤底部分');
            }
            
            const puzzleText = solutionParts[0].trim();
            const puzzleName = fileName.replace('.md', '');
            
            chatContainer.innerHTML = '';
            
            const puzzleDiv = document.createElement('div');
            puzzleDiv.className = 'puzzle-section';
            puzzleDiv.innerHTML = `
                <h3>${puzzleName}</h3>
                <div class="puzzle-text">${puzzleText}</div>
            `;
            chatContainer.appendChild(puzzleDiv);
            
            const hintDiv = document.createElement('div');
            hintDiv.className = 'hint-section';
            hintDiv.innerHTML = `
                你可以通过提问来获取线索，问题请用"是/不是"能回答的形式。<br>
                当你想猜测汤底时，请以"汤底"开头描述你的推理。
            `;
            chatContainer.appendChild(hintDiv);
            cluesGiven = [];
            saveState();
        } catch (error) {
            chatContainer.innerHTML = `<div class="error">加载谜题失败: ${error.message}</div>`;
        }
    }
    
    async function loadRandomPuzzle() {
        try {
            const response = await fetch('/puzzles/');
            const text = await response.text();
            
            const parser = new DOMParser();
            const htmlDoc = parser.parseFromString(text, 'text/html');
            const links = htmlDoc.querySelectorAll('a[href$=".md"]');
            
            if (links.length === 0) {
                throw new Error('没有找到任何谜题文件');
            }
            
            const randomIndex = Math.floor(Math.random() * links.length);
            const randomFile = links[randomIndex].getAttribute('href');
            
            await loadPuzzle(randomFile);
        } catch (error) {
            chatContainer.innerHTML = `<div class="error">加载随机谜题失败: ${error.message}</div>`;
        }
    }

    // 处理用户输入
    submitBtn.addEventListener('click', async function handleSubmit() {
        if (!currentPuzzle) {
            addMessage('请先加载一个谜题', 'error');
            return;
        }
        
        const input = userInput.value.trim();
        if (!input) return;
        
        const waitingSpan = addMessage(input, 'user');
        lockUI();
        
        try {
            let response;
            if (input.startsWith('汤底') || input.startsWith("汤底：")) {
                response = await checkSolution(input.replace(/^汤底[:：]?\s*/, ''));
            } else {
                response = await answerQuestion(input);
            }
            addMessage(response, 'bot', waitingSpan.id);
            saveState();
        } catch (error) {
            addMessage(`处理失败: ${error.message}`, 'error', 'waiting-message');
        } finally {
            unlockUI();
            userInput.value = '';
        }
    });

    // 回答问题
    async function answerQuestion(question) {
        try {
            const messages = [
                { role: "system", content: `你是一个海龟汤游戏主持人，根据以下谜题和规则回答问题：
谜题: ${currentPuzzle}
规则:
1. 先对谜题和问题进行简单分析，然后再给出回答
2. 回答必须用"{是}"、"{不是}"、"{是也不是}"或"{没有关系}"格式
3. 如果问题部分正确回答"{是也不是}"
4. 如果问题与谜题无关回答"{没有关系}"` },
                { role: "user", content: question }
            ];
            
            const response = await callOpenRouterAPI(messages);
            
            window.lastAPIResponse = {
                request: messages,
                response: response
            };
            
            const answerMatch = response.match(/\{(.*?)\}/);
            const answer = answerMatch ? answerMatch[1] : response;
            
            cluesGiven.push({question, answer});
            return answer;
        } catch (error) {
            throw new Error(`回答问题时出错: ${error.message}`);
        }
    }

    // 验证谜底
    async function checkSolution(solution) {
        try {
            const messages = [
                {
                    role: "system", content: `你是一个海龟汤游戏主持人，根据以下谜题验证猜题者的答案：
谜题: ${currentPuzzle}
规则:
1. 先对谜题和猜题者的答案进行简单分析，然后再给出判断结果
2. 判断结果必须用"{完全正确}"、"{部分正确}"或"{完全错误}"格式
3. 可以指出错误或遗漏的部分` },
                { role: "user", content: `汤底: ${solution}` }
            ];

            const response = await callOpenRouterAPI(messages);
            window.lastAPIResponse = {
                request: messages,
                response: response
            };
            
            const resultMatch = response.match(/\{(.*?)\}/);
            const result = resultMatch ? resultMatch[1] : response;
            
            if (result === '完全正确') {
                const correctDiv = document.createElement('div');
                correctDiv.innerHTML = `
                    <span style="font-weight:bold;color:green">完全正确！！！</span>
                    <div>${'谜底：' + currentPuzzle.match(/### 汤底([\s\S]*?)(###|$)/)[1].trim()}</div>
                `;
                chatContainer.appendChild(correctDiv);
                return '';
            }
            return result;
        } catch (error) {
            throw new Error(`验证谜底时出错: ${error.message}`);
        }
    }

    // 调用OpenRouter API
    async function callOpenRouterAPI(messages) {
        const response = await fetch(OPENROUTER_API_URL, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
                'HTTP-Referer': window.location.href,
                'X-Title': encodeURIComponent('海龟汤AI助手'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: `${DEFAULT_MODEL}`,
                messages: messages,
                temperature: 0.7
            })
        });

        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }

        const data = await response.json();
        return data.choices[0].message.content;
    }

    // 添加消息到聊天界面
    function addMessage(text, type, replaceId = null) {
        const container = document.createElement('div');
        container.className = 'message-container';
        
        if (type === 'user') {
            const userSpan = document.createElement('span');
            userSpan.className = 'user-message';
            userSpan.textContent = text;
            container.appendChild(userSpan);
            
            const waitingSpan = document.createElement('span');
            waitingSpan.className = 'waiting-message';
            waitingSpan.id = `waiting-${Date.now()}`;
            waitingSpan.textContent = ' - 等待中...';
            container.appendChild(waitingSpan);
            
            chatContainer.appendChild(container);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return waitingSpan;
        } else {
            let responseClass = '';
            const trimmedText = text.trim();
            if (trimmedText === '是') {
                responseClass = 'response-yes';
            } else if (trimmedText === '不是') {
                responseClass = 'response-no';
            } else if (trimmedText === '没有关系') {
                responseClass = 'response-neutral';
            }
            
            if (replaceId) {
                const waitingElement = document.getElementById(replaceId);
                if (waitingElement) {
                    const container = waitingElement.parentNode;
                    const responseSpan = document.createElement('span');
                    responseSpan.className = responseClass;
                    responseSpan.textContent = ` - ${text}`;
                    
                    if (window.lastAPIResponse) {
                        const debugDiv = document.createElement('div');
                        debugDiv.style.display = 'none';
                        debugDiv.textContent = `完整响应: ${JSON.stringify(window.lastAPIResponse, null, 2)}`;
                        container.appendChild(debugDiv);
                    }
                    
                    container.replaceChild(responseSpan, waitingElement);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    return responseSpan;
                }
            }
            
            const responseSpan = document.createElement('span');
            responseSpan.className = responseClass;
            responseSpan.textContent = text;
            container.appendChild(responseSpan);
            
            if (window.lastAPIResponse) {
                const debugDiv = document.createElement('div');
                debugDiv.style.display = 'none';
                debugDiv.textContent = `完整响应: ${JSON.stringify(window.lastAPIResponse, null, 2)}`;
                container.appendChild(debugDiv);
            }
            
            chatContainer.appendChild(container);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return container;
        }
    }
});
