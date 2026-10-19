function serializeNode(element){
    const isSelected = element.classList.contains('selected');
    if(element.classList.contains('lexical-item')){
        const labelElement = element.querySelector('.syntax-label');
        const inputElement = element.querySelector('.word-input');
        
        let nodeText = labelElement ? labelElement.innerText : element.innerText;
        let wordText = inputElement ? inputElement.value.trim() : "";

        return {
            type : "terminal",
            text : nodeText,
            word : wordText,
            selected : isSelected,
            isTrace : element.classList.contains('trace-node') || nodeText.includes('_t')
        };
    }
    if(element.classList.contains('tree-node')){
        const labelText = element.querySelector('.node-label').innerText;
        const children = element.querySelector('.node-children').children;
        
        return {
            type : "non-terminal",
            label : labelText,
            isTrace : labelText.includes('_t'),
            left : serializeNode(children[0]),
            right : serializeNode(children[1]),
            selected : isSelected
        };
    }
}

// Calculates the closest element to the right of the mouse cursor on the X-axis
function getDragAfterElement(container, x) {
    /**
     * selecting all the lexical-item/tree-node that are *direct children* of the current scope (via > operator)
     * and spreading it into an array (via ... operator)
     */
    const draggableElements = [...container.querySelectorAll(':scope > .lexical-item, :scope > .tree-node')];

    /**
     * Reducing the draggable elements to a single (closest from the right) candidate
     * closest = current closest element, child = current candidate
     */
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect(); // Gets the geometry of the box
        const offset = x - box.left - box.width / 2; // Distance from the center of the box

        // If the mouse is to the left of the box's center, it's a valid target
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}


//Finding all items with the class "lexical-item"
const lexicalItems = document.querySelectorAll('.lexical-item');

lexicalItems.forEach(item=>{
    //For every lexical item, adding an event listener for the event of starting to drag
    item.addEventListener('dragstart', (event)=>{
        console.log("Drag initiated for:", event.target.innerText);
        event.dataTransfer.setData('text/plain', event.target.innerText); //Saving the text in the temporary drag memory
    });
});

const canvas = document.getElementById("canvas");
canvas.addEventListener('dragover', (event) => {
    event.preventDefault(); //Allowing the canvas to be dropped upon
});
canvas.addEventListener('drop', (event) => {
    event.preventDefault();

    //Creating a duplicate of the dragged node using the data from the drag memory
    const itemText = event.dataTransfer.getData('text/plain');
    const newNode = document.createElement('div');
    newNode.className = 'lexical-item';
    
    const labelSpan = document.createElement('span');
    labelSpan.className = "syntax-label";
    labelSpan.innerText = itemText;

    const wordInput = document.createElement('input');
    wordInput.type = "text";
    wordInput.className = "word-input";
    wordInput.placeholder = 'word...';

    wordInput.addEventListener('click', (e) => e.stopPropagation());

    newNode.appendChild(labelSpan);
    newNode.appendChild(wordInput);

    const placeholder = canvas.querySelector('.placeholder-text'); //Removing the placeholder text of the data, if it exists
    if(placeholder){
        placeholder.remove();
    }

    // Determine the spatial insertion point based on the mouse's X-coordinate
    const afterElement = getDragAfterElement(canvas, event.clientX);
    if (!afterElement) {
        canvas.appendChild(newNode); // Drop at the very end
    } else {
        canvas.insertBefore(newNode, afterElement); // Insert right before the closest element
    }
    console.log('Merged into workspace: ',itemText);
});

canvas.addEventListener('click', (event) => {
    const target = event.target.closest('.tree-node, .lexical-item'); // The target is the closest tree-node/lexical/item to the click position
    if(target){
        event.stopPropagation(); // Only the item itself is clicked, not its parent
        target.classList.toggle('selected');
    }
});

/**
 * MERGE BUTTON
 */
const mergeBtn = document.getElementById("merge-btn");
 mergeBtn.addEventListener('click', () => {
    const selectedNodes = document.querySelectorAll('.lexical-item.selected, .tree-node.selected');

    if(selectedNodes.length != 2){
        statusText.innerText = "CRASH: Merge is a binary operation. Please select exactly two items.";
        statusText.style.color = "red";
        return;
    }

    if(selectedNodes[0].parentElement !== canvas || selectedNodes[1].parentElement !== canvas){
        statusText.innerText = "CRASH: Extension Condition violation. External Merge must target root nodes in the workspace."
        statusText.style.color = "red";
        selectedNodes.forEach(node => node.classList.remove('selected'));
        return;
    }

    const item1 = serializeNode(selectedNodes[0]);
    const item2 = serializeNode(selectedNodes[1]);
    const payload = {items: [item1, item2]};

    fetch("http://127.0.0.1:5000/api/merge", {
        method: "POST",
        headers: {
            'Content-Type': "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok){
            throw new Error(data.message);
        }
        return data;
    })
    .then(data => {
        statusText.innerText = data.message;
        statusText.style.color = "#27ae60";
        console.log("Merge Data: ", data);

        const treeNode = document.createElement('div');
        treeNode.className = "tree-node";
        const nodeLabel = document.createElement('div');
        nodeLabel.className = "node-label";
        nodeLabel.innerText = data.parent_label;
        const childrenContainer = document.createElement('div');
        childrenContainer.className = "node-children";

        const firstNode = selectedNodes[0];
        const canvas = document.getElementById('canvas');
        canvas.insertBefore(treeNode, firstNode);

        selectedNodes.forEach(node =>{
            node.classList.remove('selected');
            childrenContainer.appendChild(node);
        });

        treeNode.appendChild(nodeLabel);
        treeNode.appendChild(childrenContainer);
    })
    .catch(error => {
        statusText.innerText = error.message;
        statusText.style.color = "red";
    })
 })

/**
 * AGREE BUTTON
 */
const agreeBtn = document.getElementById('agree-btn');

agreeBtn.addEventListener('click', () => {
    statusText.innerText = "Initiaing Agree...";
    statusText.style.color = "#333";
    
    const selectedNodes = document.querySelectorAll('.lexical-item.selected, .tree-node.selected');
    if(selectedNodes.length != 1){
        statusText.innerText = "CRASH: Agree requires exactly one selected probe node";
        statusText.style.color = "red";
        return;
    }

    const probeNode = selectedNodes[0];
    const payload = {tree: serializeNode(probeNode)};

    fetch("http://127.0.0.1:5000/api/agree", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(async response => {
        const data = await response.json();
        if(!response.ok){
            throw new Error(data.message);
        }
        return data;
    })
    .then(data => {
        statusText.innerText = data.message;
        statusText.style.color = "#27ae60";
        if(data.updated_text) {
            let headNode;
            if (probeNode.classList.contains('tree-node')){
                headNode = probeNode.querySelector('.lexical-item');
            } else {
                headNode = probeNode;
            }

            const labelSpan = headNode.querySelector('.syntax-label');
            if (labelSpan) {
                labelSpan.innerText = data.updated_text;
            } else {
            headNode.innerText = data.updated_text;
            }
        }

        probeNode.classList.remove('selected');
    })
    .catch(error => {
        statusText.innerText = error.message;
        statusText.style.color = "red";
    });
});

/**
 * MOVE BUTTON
 */
const moveBtn = document.getElementById('move-btn');

moveBtn.addEventListener('click', () => {
    statusText.innerText = "Initiating Internal Merge...";
    statusText.style.color = "#333";

    const selectedNodes = document.querySelectorAll('.lexical-item.selected, .tree-node.selected');
    if(selectedNodes.length !== 1){
        statusText.innerText = "CRASH: Move requires exactly one selected item (the goal)";
        statusText.style.color = "red";
        return;
    }

    const goalNode = selectedNodes[0];

    let rootNode = goalNode;
    while(rootNode.parentElement && rootNode.parentElement !== canvas){
        rootNode = rootNode.parentElement;
    }

    if(rootNode.parentElement !== canvas){
        statusText.innerText = "CRASH: Goal must be inside a tree on the workspace";
        statusText.style.color = "red";
        return;
    }
    if(goalNode === rootNode){
        statusText.innerText = "CRASH: Cannot internally merge a root node with itself";
        statusText.style.color = "red";
        return;
    }

    const payload = {tree: serializeNode(rootNode)};
    fetch("http://127.0.0.1:5000/api/move", {
        method: "POST",
        headers: {'Content-Type': "application/json"},
        body: JSON.stringify(payload)
    })
    .then(async response => {
        const data = await response.json();
        if(!response.ok)
            throw new Error(data.message);
        return data;
    })
    .then(data => {
        statusText.innerText = data.message;
        statusText.style.color = "#27ae60";

        const treeNode = document.createElement('div');
        treeNode.className = "tree-node";

        const nodeLabel = document.createElement('div');
        nodeLabel.className = "node-label";
        nodeLabel.innerText = data.parent_label;

        const childrenContainer = document.createElement('div');
        childrenContainer.className = "node-children";

        const movedSpecifier = goalNode.cloneNode(true);
        movedSpecifier.classList.remove('selected');
        const originalInput = goalNode.querySelector('.word-input');
        const clonedInput = movedSpecifier.querySelector('.word-input');
        if (originalInput && clonedInput) {
            clonedInput.value = originalInput.value;
        }

        if(goalNode.classList.contains('lexical-item')){
            const baseLabel = goalNode.innerText.split(' ')[0];
            goalNode.innerText = baseLabel + "_t";
        }
        else if(goalNode.classList.contains('tree-node')){
            const labelDiv = goalNode.querySelector('.node-label');
            labelDiv.innerText = labelDiv.innerText + "_t";
        }
        goalNode.classList.add('trace-node');
        goalNode.classList.remove('selected');

        canvas.insertBefore(treeNode, rootNode);
        childrenContainer.appendChild(movedSpecifier);
        childrenContainer.appendChild(rootNode);

        treeNode.appendChild(nodeLabel);
        treeNode.appendChild(childrenContainer);
    })
    .catch(error => {
        statusText.innerText = error.message;
        statusText.style.color = "red";
        goalNode.classList.remove('selected');
    });
});


/**
 * VALIDATE BUTTON
 */
const validateBtn = document.getElementById('validate-btn');
const statusText = document.getElementById('status-text');

validateBtn.addEventListener('click', () => {
    statusText.innerText = "sending Derivation...";
    statusText.style.color = "#333";

    const canvas = document.getElementById('canvas');
    const rootElements = Array.from(canvas.children).filter(child =>
        child.classList.contains('lexical-item') || child.classList.contains('tree-node')
    );

    if (rootElements.length === 0) {
        statusText.innerText = "CRASH: The derivation board is empty.";
        statusText.style.color = "red";
        return;
    }
    if (rootElements.length > 1) {
        statusText.innerText = "CRASH: Multiple unconnected objects on the board. Merge into a single root node.";
        statusText.style.color = "red";
        return;
    }

    const serializedTree = serializeNode(rootElements[0]);
    const payload = {tree: serializedTree}
    console.log("Serialized Tree Payload: ", payload);

    fetch('http://127.0.0.1:5000/api/validate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(async response => {
        // Parse the JSON data first, regardless of success or error
        const data = await response.json();
        
        if (!response.ok) {
            // If Python sent a 400 error, throw the custom message from the backend
            throw new Error(data.message);
        }
        return data;
    })
    .then(data => {
        console.log("Server replied: ", data);
        statusText.innerText = data.message;
        if(data.converged){
            statusText.style.color = "#27ae60";
        } else {
            statusText.style.color = "red";
        }
    })
    .catch(error => {
        console.error("Validation Failed:", error.message);
        // This line physically injects the Python error text into the HTML
        statusText.innerText = error.message; 
        statusText.style.color = "red";
    });
});

/**
 * RESET BUTTON
 */
const resetBtn = document.getElementById('reset-btn');
resetBtn.addEventListener('click', () => {
    const canvas = document.getElementById('canvas');
    canvas.innerHTML= '<p class="placeholder-text">Drag lexical items here to start external merge</p>';

    statusText.innerText = "Workspace reset";
    statusText.style.color = "#333";
});

/**
 * DELETE BUTTON
 */
const deleteBtn = document.getElementById('delete-btn');

deleteBtn.addEventListener('click', () => {
    const selectedNodes = document.querySelectorAll('.lexical-item.selected, .tree-node.selected');
    
    if (selectedNodes.length !== 1) {
        statusText.innerText = "CRASH: Please select exactly one item to delete or unmerge.";
        statusText.style.color = "red";
        return;
    }

    const targetNode = selectedNodes[0];

    // Enforce top-down dismantling to protect the binary graph
    if (targetNode.parentElement !== canvas) {
        statusText.innerText = "CRASH: Can only modify root nodes on the workspace. Unmerge from the top down.";
        statusText.style.color = "red";
        targetNode.classList.remove('selected');
        return;
    }

    if (targetNode.classList.contains('lexical-item')) {
        // Delete a standalone lexical item
        targetNode.remove();
        statusText.innerText = "Item deleted from workspace.";
        statusText.style.color = "#333";
    } else if (targetNode.classList.contains('tree-node')) {
        // Unmerge a tree: move children back to the canvas, then destroy the parent
        const childrenContainer = targetNode.querySelector('.node-children');
        
        while (childrenContainer.firstChild) {
            canvas.insertBefore(childrenContainer.firstChild, targetNode);
        }
        
        targetNode.remove();
        statusText.innerText = "Node unmerged. Children returned to workspace.";
        statusText.style.color = "#333";
    }
});

// ==========================================
// EXPORT TO JSON
// ==========================================
const exportJsonBtn = document.getElementById('export-json-btn');

exportJsonBtn.addEventListener('click', () => {
    const canvas = document.getElementById('canvas');
    const rootElements = Array.from(canvas.children).filter(child =>
        child.classList.contains('lexical-item') || child.classList.contains('tree-node')
    );

    if (rootElements.length !== 1) {
        statusText.innerText = "CRASH: Please merge the board into a single root node before exporting.";
        statusText.style.color = "red";
        return;
    }

    const serializedTree = serializeNode(rootElements[0]);
    const jsonString = JSON.stringify(serializedTree, null, 2); 
    
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "minimalist_derivation.json";
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    statusText.innerText = "Derivation exported to JSON.";
    statusText.style.color = "#333";
});

// ==========================================
// EXPORT TO LATEX (FOREST PACKAGE)
// ==========================================
const exportLatexBtn = document.getElementById('export-latex-btn');

// Helper to escape LaTeX special characters
function cleanLaTeX(text) {
    if (!text) return "";
    return text
        .replace(/\\/g, "")           
        .replace(/_/g, "\\_")         
        .replace(/φ|phi/g, "$\\phi$") 
        .trim();
}

// Global trackers for movement arrows
let traceCounter = 0;
let specCounter = 0;

function buildForestString(node, indent = "  ") {
    let nameTag = "";
    
    // Tag Traces (Bottom of the tree)
    if (node.isTrace) {
        traceCounter++;
        nameTag = `, name=trace${traceCounter}`;
    }
    // Tag Landing Sites (Top of the tree)
    else if (node.isLandingSite) {
        specCounter++;
        nameTag = `, name=spec${specCounter}`;
    }

    if (node.type === "terminal") {
        let terminalContent = cleanLaTeX(node.text);
        
        if (node.word) {
            const cleanWord = cleanLaTeX(node.word);
            return `${indent}[{${terminalContent}}${nameTag}\n${indent}  [{\\textit{${cleanWord}}}]\n${indent}]`;
        }
        return `${indent}[{${terminalContent}}${nameTag}]`;
    }

    const cleanLabel = cleanLaTeX(node.label);
    
    // Pre-tag the left child (Specifier) if this is a major projection
    if ((node.label === "TP" || node.label === "vP") && node.left && !node.left.isTrace) {
        node.left.isLandingSite = true;
    }

    const leftLatex = buildForestString(node.left, indent + "  ");
    const rightLatex = buildForestString(node.right, indent + "  ");
    
    return `${indent}[{${cleanLabel}}${nameTag}\n${leftLatex}\n${rightLatex}\n${indent}]`;
}

exportLatexBtn.addEventListener('click', () => {
    const canvas = document.getElementById('canvas');
    const rootElements = Array.from(canvas.children).filter(child =>
        child.classList.contains('lexical-item') || child.classList.contains('tree-node')
    );

    if (rootElements.length !== 1) {
        statusText.innerText = "CRASH: Please merge the board into a single root node before exporting.";
        statusText.style.color = "red";
        return;
    }

    // Reset movement tracking state before every export
    traceCounter = 0;
    specCounter = 0;

    const serializedTree = serializeNode(rootElements[0]);
    const latexTree = buildForestString(serializedTree);

    // Build TikZ arrow commands if movement occurred
    let arrowCommands = "";
    if (traceCounter > 0) {
        arrowCommands = `\n  % Movement Arrows\n`;
        // Draw an arrow for each trace/specifier pair found
        let maxArrows = Math.min(traceCounter, specCounter);
        for (let i = 1; i <= maxArrows; i++) {
            arrowCommands += `  \\draw[->, dashed, thick, bend left=45] (trace${i}.south) to (spec${i}.south);\n`;
        }
    }

    const fullLatexCode = `\\begin{forest}\nfor tree={s sep=1.5em, l sep=1.8em}\n${latexTree}${arrowCommands}\\end{forest}`;

    navigator.clipboard.writeText(fullLatexCode).then(() => {
        statusText.innerText = "LaTeX code copied to clipboard! (Don't forget \\usepackage{forest})";
        statusText.style.color = "#27ae60";
    }).catch(err => {
        statusText.innerText = "CRASH: Failed to copy to clipboard.";
        statusText.style.color = "red";
    });
});