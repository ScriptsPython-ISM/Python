
const fs = require("fs")

async function getGlobleAnswer() {
  const today = new Date().toISOString().split('T')[0];
  const listLength = 197;
  const response = await fetch(`https://globle-game.com/answer?day=${today}&list=${listLength}`);
  
  if (!response.ok) {
    throw new Error(`HTTP error! Status: ${response.status}`);
  }
  
  const data = await response.json();
  return data.answer;
}

decrypted = getGlobleAnswer()
  .then(answer => {
    fs.writeFileSync("C:/Users/pmcgi/OneDrive/Desktop/Visual Studio/wordle/globle.txt", answer);
  })
  .catch(error => {console.error('Error fetching the Globle answer:', error)});