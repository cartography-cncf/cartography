document.addEventListener("DOMContentLoaded", () => {
  const link = document.querySelector('.globaltoc a[href$="module-list.html"]');
  const item = link?.parentElement;

  if (item?.classList.contains("_collapse")) {
    item.querySelector(":scope > button")?.click();
  }
});
