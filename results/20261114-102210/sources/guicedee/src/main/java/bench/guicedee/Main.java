package bench.guicedee;
import com.guicedee.client.IGuiceContext;
import com.guicedee.guicedinjection.GuiceApplication;

public class Main {
    public static void main(String[] args) {
        GuiceApplication.run(() -> {
            IGuiceContext.registerModule(Main.class);
            IGuiceContext.instance().getConfig().setServiceLoadWithClassPath(false);
        });
    }
}
