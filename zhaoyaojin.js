#取消标题栏中'教师'的注释
let temp=document.querySelector("body > main > div > div.container-fluid > div:nth-child(3) > div > div.panel.panel-primary.filterable > div.panel-body > table > tbody:nth-child(1) > tr")
htmltext=temp.innerHTML
htmltext=htmltext.replace(/<!--\s?(.*?)\s?-->/g, '$1');
temp.innerHTML=htmltext
#遍历表格内容的所有节点，取消其中的教师名称注释
for (let i = 1; i <= document.querySelector("body > main > div > div.container-fluid > div:nth-child(3) > div > div.panel.panel-primary.filterable > div.panel-body > table > tbody:nth-child(2)").children.length; i++) {
     temp = document.querySelector(`body > main > div > div.container-fluid > div:nth-child(3) > div > div.panel.panel-primary.filterable > div.panel-body > table > tbody:nth-child(2) > tr:nth-child(${i})`);
    
    if (temp) {
        let htmltext = temp.innerHTML;
        htmltext = htmltext.replace(/<!--\s?(.*?)\s?-->/g, '$1');
        temp.innerHTML = htmltext;
    }
}
