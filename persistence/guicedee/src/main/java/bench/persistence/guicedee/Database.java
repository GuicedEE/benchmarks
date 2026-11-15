package bench.persistence.guicedee;

import com.guicedee.persistence.ConnectionBaseInfo;
import com.guicedee.persistence.DatabaseModule;
import com.guicedee.persistence.implementations.postgres.PostgresConnectionBaseInfo;
import org.hibernate.jpa.boot.spi.PersistenceUnitDescriptor;

import java.util.Properties;

public class Database extends DatabaseModule<Database> {
    protected String getPersistenceUnitName() { return "bench"; }
    protected ConnectionBaseInfo getConnectionBaseInfo(PersistenceUnitDescriptor unit, Properties properties) {
        var info = new PostgresConnectionBaseInfo();
        info.setReactive(true); info.setDefaultConnection(true);
        info.setMinPoolSize(0); info.setMaxPoolSize(5);
        return info;
    }
}
