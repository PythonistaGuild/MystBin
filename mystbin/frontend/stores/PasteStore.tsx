import { EventEmitter } from "events";
import pasteDispatcher from "../dispatchers/PasteDispatcher";


const CHANGE_EVENT = "change";
let _paste;

class PasteStore extends EventEmitter {
    addChangeListener(callback) {
        this.on(CHANGE_EVENT, callback);
    }

    removeChangeListener(callback) {
        this.removeListener(CHANGE_EVENT, callback);
    }

    emitChange() {
        this.emit(CHANGE_EVENT);
    }

    getPaste() {
        return _paste;
    }
}


pasteDispatcher.register((action) => {
    _paste = action.paste;
    pasteStore.emitChange();
})

const pasteStore = new PasteStore();
export default pasteStore;